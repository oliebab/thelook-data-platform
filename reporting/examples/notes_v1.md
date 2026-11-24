# Notes on prompt v1 (real data, weeks of 26 Oct – 16 Nov 2026)

Week of 16 Nov (guardrail passed):
1. Raw number formatting: "329195.9 USD". v2: write money as $329,195.90 and counts with thousands separators. The guardrail already accepts `$` and commas.
2. "What went well" repeats the headline (net revenue and orders appear twice). v2: bullets must not repeat the headline items.
3. Mixed message: the wins celebrate +194% while the last note says to read large increases in the latest week with caution. v2: when that note is present, mention it next to the headline, not at the end of Things to watch.
4. Things to watch has 6 bullets (3 KPIs + 3 notes). v2: move `notes` into their own short "Data caveats" section.
5. Suggested actions claim causes ("friction points driving the rise") and one is about our pipeline ("validate data pipeline models"), not the business. v2: each action is something to investigate, tied to one highlighted item, about the business only.
Weeks of 26 Oct, 2 Nov, 9 Nov (guardrail passed on all 4):
6. Layout varies between weeks: `*` vs `-` bullets, and on 2 Nov the notes are plain lines outside the list. v2: give an exact output template (fixed bullet marker, notes as a list in their own section).
7. The headline drifts from the agreed order: on 9 Nov the second clause is gross revenue, which only repeats net revenue. v2: headline = net revenue + the most important highlighted item that is NOT revenue.
8. Actions not tied to a highlighted item: on 9 Nov, two actions restate the data caveats, and one cites Outerwear & Coats, which the review never mentions. v2: every action names the highlighted item it follows from; caveats never become actions.
