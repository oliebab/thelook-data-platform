import re
import json
from datetime import date, datetime


def check_numbers(output_md, kpi_json):
    """
    Return numbers in output_md that are not present in kpi_json.

    Allowed:
    - All numeric values found in the KPI JSON.
    - Their rounded representations (0, 1, and 2 decimal places).
    - Numbers appearing in period dates.
    - Single-digit numbers used in phrases such as 'top 3'.
    """

    def normalise(value):
        return float(
            str(value)
            .replace(",", "")
            .replace("%", "")
            .replace("$", "")
        )

    def extract_numbers(text):
        pattern = r'(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?'
        return re.findall(pattern, text)

    # Parse JSON if supplied as a string
    if isinstance(kpi_json, str):
        kpi_json = json.loads(kpi_json)

    allowed_numbers = set()

    def collect_json_numbers(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Capture period/date values separately
                if any(term in key.lower() for term in ("date", "period")):
                    if isinstance(value, str):
                        for number in extract_numbers(value):
                            try:
                                allowed_numbers.add(normalise(number))
                            except ValueError:
                                pass

                collect_json_numbers(value)

        elif isinstance(obj, list):
            for item in obj:
                collect_json_numbers(item)

        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            allowed_numbers.add(float(obj))

        elif isinstance(obj, str):
            for number in extract_numbers(obj):
                try:
                    allowed_numbers.add(normalise(number))
                except ValueError:
                    pass

    collect_json_numbers(kpi_json)

    # Add rounded representations of all allowed numbers
    expanded_allowed = set()

    for number in allowed_numbers:
        expanded_allowed.add(number)
        for decimals in (0, 1, 2):
            expanded_allowed.add(round(number, decimals))

    # Extract numbers from the review
    unexpected_numbers = []

    for match in extract_numbers(output_md):
        try:
            number = normalise(match)
        except ValueError:
            continue

        # Ignore single-digit numbers (e.g. "top 3")
        if abs(number) < 10 and number.is_integer():
            continue

        if number not in expanded_allowed:
            unexpected_numbers.append(str(normalise(match)).rstrip("0").rstrip(".")
                         if "." in str(normalise(match))
                         else str(int(normalise(match))))

    return unexpected_numbers