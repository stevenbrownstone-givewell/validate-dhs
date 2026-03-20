#!/usr/bin/env python3
"""
dhs_api.py — Query the DHS Program REST API.

Subcommands:
  surveys <country_code>              List available surveys
  indicators <search_term>            Search indicators by keyword
  data <country> <survey> <ids>       Get official indicator values

Uses only Python stdlib (no pip dependencies).
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "https://api.dhsprogram.com/rest/dhs"
TIMEOUT = 30


def api_get(endpoint, params=None):
    """Make a GET request to the DHS API."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        params["f"] = "json"
        url += "?" + urllib.parse.urlencode(params)
    else:
        url += "?f=json"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dhs-validate/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(f"URL: {url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def resolve_survey_id(country_code, year_or_id):
    """Resolve a year to a survey ID, or validate an existing survey ID."""
    # If it looks like a survey ID already (contains letters), validate it
    if any(c.isalpha() for c in year_or_id):
        return year_or_id

    # It's a year — look up matching surveys
    year = int(year_or_id)
    result = api_get("surveys", {"countryIds": country_code})
    data = result.get("Data", [])

    matches = []
    for s in data:
        try:
            sy = int(s.get("SurveyYear", 0))
        except (ValueError, TypeError):
            continue
        # DHS surveys can span two years (e.g., 2023-24 listed as 2023)
        if sy == year or sy == year - 1:
            matches.append(s)

    if not matches:
        print(f"No surveys found for {country_code} around year {year}.", file=sys.stderr)
        print("Available surveys:", file=sys.stderr)
        for s in data:
            print(f"  {s['SurveyId']}  {s.get('SurveyYearLabel', s['SurveyYear'])}  {s['SurveyType']}", file=sys.stderr)
        sys.exit(1)

    if len(matches) == 1:
        sid = matches[0]["SurveyId"]
        print(f"Resolved year {year} -> {sid} ({matches[0].get('SurveyYearLabel', '')})", file=sys.stderr)
        return sid

    # Multiple matches — prefer DHS over MIS/AIS
    dhs_matches = [m for m in matches if m["SurveyType"] == "DHS"]
    if len(dhs_matches) == 1:
        sid = dhs_matches[0]["SurveyId"]
        print(f"Resolved year {year} -> {sid} (selected DHS over other survey types)", file=sys.stderr)
        return sid

    print(f"Multiple surveys found for {country_code} around year {year}:", file=sys.stderr)
    for s in matches:
        print(f"  {s['SurveyId']}  {s.get('SurveyYearLabel', s['SurveyYear'])}  {s['SurveyType']}", file=sys.stderr)
    print("Please specify the exact SurveyId.", file=sys.stderr)
    sys.exit(1)


# ── Subcommands ───────────────────────────────────────────────────────────────

def cmd_surveys(args):
    """List available surveys for a country."""
    result = api_get("surveys", {"countryIds": args.country_code})
    data = result.get("Data", [])

    if not data:
        print(f"No surveys found for country code '{args.country_code}'.")
        return

    # Print header
    print(f"{'SurveyId':<16} {'Year':<12} {'Type':<8} {'HHs':>8} {'Women':>8} {'Men':>8}")
    print("-" * 72)

    for s in sorted(data, key=lambda x: x.get("SurveyYear", 0)):
        print(f"{s['SurveyId']:<16} "
              f"{s.get('SurveyYearLabel', str(s['SurveyYear'])):<12} "
              f"{s.get('SurveyType', ''):<8} "
              f"{s.get('NumberOfHouseholdsListed', ''):>8} "
              f"{s.get('NumberOfWomenEligibleInterviewed', ''):>8} "
              f"{s.get('NumberOfMenEligibleInterviewed', ''):>8}")


def cmd_indicators(args):
    """Search indicators by keyword."""
    result = api_get("indicators", {
        "returnFields": "IndicatorId,Label,ShortName"
    })
    data = result.get("Data", [])

    term = args.search_term.lower()
    matches = []
    for ind in data:
        searchable = f"{ind.get('IndicatorId', '')} {ind.get('Label', '')} {ind.get('ShortName', '')}".lower()
        if term in searchable:
            matches.append(ind)

    if not matches:
        print(f"No indicators matching '{args.search_term}'.")
        return

    print(f"Found {len(matches)} indicators matching '{args.search_term}':\n")
    print(f"{'IndicatorId':<20} {'ShortName':<30} Label")
    print("-" * 90)

    for ind in sorted(matches, key=lambda x: x.get("IndicatorId", "")):
        iid = ind.get("IndicatorId", "")
        short = ind.get("ShortName", "")[:28]
        label = ind.get("Label", "")
        print(f"{iid:<20} {short:<30} {label}")


def cmd_data(args):
    """Get official indicator values."""
    survey_id = resolve_survey_id(args.country_code, args.survey)
    indicator_ids = args.indicator_ids

    params = {
        "countryIds": args.country_code,
        "surveyIds": survey_id,
        "indicatorIds": indicator_ids,
    }
    if args.breakdown:
        params["breakdown"] = args.breakdown

    result = api_get("data", params)
    data = result.get("Data", [])

    if not data:
        print(f"\nNo data found for survey={survey_id}, indicators={indicator_ids}.")
        print("This survey may not yet be published in STATcompiler.")
        print("Check: https://www.statcompiler.com/")
        return

    if args.json:
        print(json.dumps(data, indent=2))
        return

    # Group by indicator, then by characteristic
    # For national totals, filter to CharacteristicCategory == "Total"
    national = [d for d in data if d.get("CharacteristicCategory") == "Total"
                or d.get("CharacteristicLabel") == "Total"]

    if national:
        print(f"\nNational values for {survey_id}:\n")
        print(f"{'IndicatorId':<20} {'Value':>8}  Description")
        print("-" * 80)
        for d in sorted(national, key=lambda x: x.get("IndicatorId", "")):
            iid = d.get("IndicatorId", "")
            val = d.get("Value", "")
            desc = d.get("Indicator", "")[:50]
            print(f"{iid:<20} {val:>8}  {desc}")

    # If subnational breakdown requested, show those too
    subnational = [d for d in data if d.get("CharacteristicCategory") != "Total"
                   and d.get("CharacteristicLabel") != "Total"
                   and d.get("IsPreferred", 0) == 1]

    if args.breakdown == "subnational" and subnational:
        print(f"\nSubnational values:\n")
        print(f"{'IndicatorId':<20} {'Region':<25} {'Value':>8}")
        print("-" * 60)
        for d in sorted(subnational, key=lambda x: (x.get("IndicatorId", ""), x.get("CharacteristicLabel", ""))):
            iid = d.get("IndicatorId", "")
            region = d.get("CharacteristicLabel", "")[:23]
            val = d.get("Value", "")
            print(f"{iid:<20} {region:<25} {val:>8}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Query the DHS Program REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 dhs_api.py surveys CD
  python3 dhs_api.py indicators "ITN"
  python3 dhs_api.py data CD CD2023DHS ML_NETP_H_ITN,ML_NETC_C_ITN
  python3 dhs_api.py data CD 2023 ML_NETP_H_ITN
  python3 dhs_api.py data CD CD2023DHS ML_NETP_H_ITN --breakdown subnational
""")

    sub = parser.add_subparsers(dest="command", required=True)

    # surveys
    p_surveys = sub.add_parser("surveys", help="List available surveys for a country")
    p_surveys.add_argument("country_code", help="ISO 2-letter country code (e.g., CD)")

    # indicators
    p_ind = sub.add_parser("indicators", help="Search indicators by keyword")
    p_ind.add_argument("search_term", help="Search term (matches ID, label, or short name)")

    # data
    p_data = sub.add_parser("data", help="Get official indicator values")
    p_data.add_argument("country_code", help="ISO 2-letter country code")
    p_data.add_argument("survey", help="Survey ID (CD2023DHS) or year (2023)")
    p_data.add_argument("indicator_ids", help="Comma-separated indicator IDs")
    p_data.add_argument("--breakdown", choices=["national", "subnational", "all"],
                        default=None, help="Breakdown level")
    p_data.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.command == "surveys":
        cmd_surveys(args)
    elif args.command == "indicators":
        cmd_indicators(args)
    elif args.command == "data":
        cmd_data(args)


if __name__ == "__main__":
    main()
