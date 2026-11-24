
import json
import re


def check_numbers(output_md, kpi_json):
    """
    Return numbers in output_md that are not present in kpi_json.

    Allowed:
    - Numeric values found in the KPI JSON.
    - Rounded representations (0, 1, and 2 decimal places).
    - Absolute values of negative KPI changes.
    - Numbers appearing in period/date fields.
    - Single-digit integers (e.g. 'top 3') are ignored.
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
                # Capture period/date values
                if any(
                    term in key.lower()
                    for term in ("date", "period")
                ):
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

    # Expand allowed numbers to include rounded and absolute values
    expanded_allowed = set()

    for number in allowed_numbers:
        expanded_allowed.add(number)
        expanded_allowed.add(abs(number))

        for decimals in (0, 1, 2):
            expanded_allowed.add(round(number, decimals))
            expanded_allowed.add(round(abs(number), decimals))

    # Check numbers in the review
    unexpected_numbers = []

    for match in extract_numbers(output_md):
        try:
            number = normalise(match)
        except ValueError:
            continue

        # Ignore single-digit integers (e.g. "top 3")
        if abs(number) < 10 and number.is_integer():
            continue

        if number not in expanded_allowed:
            unexpected_numbers.append(
                str(int(number)) if number.is_integer() else str(number)
            )

    return unexpected_numbers
