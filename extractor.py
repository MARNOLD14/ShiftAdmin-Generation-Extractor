from bs4 import BeautifulSoup, Tag
import re
import pandas as pd
import datetime

SA_HTML_FILE = 'solver_example.html'

USER_ID_RE = re.compile(r'u([0-9]+)')
SHIFT_ID_RE = re.compile(r'sh([0-9]+)')
MONTH_YEAR_RE = re.compile(r'([a-zA-Z]+)\s+([0-9]+)')


def process_shift_row(sr: Tag):
    '''General format:
    <tr class="shiftRow">
        <td>
            <strong>SITE_NAME</strong>
            <span>SHIFT_NAME</span>
        </td>
        <td>
            <div class="divShift uUSER_ID shSHIFT_ID">
                <span class="spanShift">USER_NAME</span>
            </div>
        </td>
    </tr>
    '''
    tds = sr.find_all('td')

    # Guard: skip rows that don't have the expected structure
    if len(tds) < 2:
        return None
    if tds[0].strong is None:
        return None
    if tds[0].span is None:
        return None

    site_name = tds[0].strong.string
    shift_name = tds[0].span.string

    span_shifts = tds[1].find_all(class_='spanShift')
    if not span_shifts:
        return None

    results = []
    for spanShift in span_shifts:
        user_name = spanShift.string
        if not user_name:
            continue
        user_id_shift_id = ' '.join(spanShift.parent['class'])

        user_id_match = USER_ID_RE.search(user_id_shift_id)
        user_id = int(user_id_match[1]) if user_id_match else -1

        shift_id_match = SHIFT_ID_RE.search(user_id_shift_id)
        shift_id = int(shift_id_match[1]) if shift_id_match else -1

        # Walk up to find the calendar-normal td for day number
        day_number = None
        for t in sr.parents:
            if hasattr(t, 'attrs') and 'class' in t.attrs:
                if 'calendar-normal' in t['class']:
                    dn = t.find(class_='dayNumber')
                    if dn:
                        day_number = str(dn.contents[0]).strip()
                    break

        # Walk up to find the calendar table for month/year
        month_name = None
        year = None
        for t in sr.parents:
            if hasattr(t, 'attrs') and 'class' in t.attrs:
                if 'calendar' in t['class'] and 'calendar-normal' not in t['class']:
                    try:
                        header_text = str(t.tbody.tr.td.contents[0])
                        search_res = MONTH_YEAR_RE.search(header_text)
                        if search_res:
                            month_name = search_res[1]
                            year = int(search_res[2])
                    except (AttributeError, IndexError):
                        pass
                    break

        if not day_number or not month_name or not year:
            continue

        try:
            shift_date = datetime.datetime.strptime(
                f'{month_name} {day_number} {year}', '%B %d %Y'
            ).date()
        except ValueError:
            continue

        results.append({
            'shiftDate': shift_date,
            'monthName': month_name,
            'year': year,
            'dayNumber': day_number,
            'siteName': site_name,
            'shiftId': shift_id,
            'shiftName': shift_name,
            'userId': user_id,
            'userName': user_name
        })

    return results if results else None


def make_soup(fp) -> BeautifulSoup:
    soup = BeautifulSoup(fp, features='html.parser')
    return soup


def extract_calendar(soup: BeautifulSoup) -> pd.DataFrame:
    # Get all shift rows
    shift_rows = soup.find_all("tr", class_='shiftRow')

    # Filter out cover violations
    shift_rows = [sr for sr in shift_rows if 'CoverViolationInline' not in sr['class']]

    # Process each row; each returns a list of dicts or None
    raw = [process_shift_row(sr) for sr in shift_rows]

    # Flatten and remove None results
    shifts = [entry for result in raw if result is not None for entry in result]

    if not shifts:
    return pd.DataFrame(columns=['shiftDate', 'shiftName', 'userName', 'userId'])

shifts = shifts[['shiftDate', 'shiftName', 'userName', 'userId']]

shiftsp = (
    shifts.pivot_table(
        columns='shiftDate',
        index=['userName', 'userId'],
        values='shiftName',
        aggfunc=lambda x: ' / '.join(x)
    )
    .fillna('')
    .sort_index(axis=1)
    .sort_index(axis=0)
)

    return shiftsp


def main():
    with open(SA_HTML_FILE) as fp:
        extract_calendar(make_soup(fp))


if __name__ == '__main__':
    main()
