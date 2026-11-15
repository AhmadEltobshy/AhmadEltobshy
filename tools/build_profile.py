"""Build original, self-contained SVG artwork for Ahmad's GitHub README."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from html import escape
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
USER = 'AhmadEltobshy'

def api(path, query=None):
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        data = json.dumps({'query': query}).encode() if query else None
        request = urllib.request.Request('https://api.github.com/' + path, data=data,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-builder'})
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    else:
        command = ['gh', 'api', path]
        if query:
            command += ['-f', 'query=' + query]
        result = json.loads(subprocess.check_output(command, text=True, encoding='utf-8'))
    if isinstance(result, dict) and result.get('errors'):
        raise RuntimeError(result['errors'])
    return result

def text(x, y, value, color, size=16, weight='normal'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'

def svg(width, height, background, body, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
@font-face {{font-family:ConsolasFallback;src:local('Consolas'),local('Consolas Bold');font-display:swap;size-adjust:109%;}}
text {{font-family:ConsolasFallback,Consolas,monospace;white-space:pre}}
</style>
<rect width="{width}" height="{height}" rx="14" fill="{background}"/>
{''.join(body)}</svg>'''

def build():
    user = api('users/' + USER)
    repos = api('users/' + USER + '/repos?per_page=100')
    query = 'query { user(login:"' + USER + '") { contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount contributionLevel } } } } } }'
    calendar = api('graphql', query)['data']['user']['contributionsCollection']['contributionCalendar']
    cache = ROOT / 'assets' / 'stats.json'
    cache.write_text(json.dumps({'followers': user['followers'], 'public_repos': user['public_repos'],
        'stars': sum(r['stargazers_count'] for r in repos if not r['fork']), 'calendar': calendar}, indent=2) + '\n', encoding='utf-8')
    portrait = ET.parse(ROOT / 'assets' / 'portrait-vector.svg').getroot()
    portrait_scale = min(360 / float(portrait.attrib['width']), 500 / float(portrait.attrib['height']))
    portrait_x = 15 + (360 - float(portrait.attrib['width']) * portrait_scale) / 2
    portrait_y = 15 + (500 - float(portrait.attrib['height']) * portrait_scale) / 2
    profile = json.loads((ROOT / 'assets' / 'profile.json').read_text(encoding='utf-8'))
    for theme, bg, fg, muted, accent, value, levels in [
        ('dark', '#161b22', '#c9d1d9', '#616e7f', '#ffa657', '#a5d6ff', ['#242d38','#0e4429','#006d32','#26a641','#39d353']),
        ('light', '#f6f8fa', '#24292f', '#6e7781', '#b64b08', '#0550ae', ['#e6e9ed','#9be9a8','#40c463','#30a14e','#216e39'])]:
        body = []
        paths = []
        for path in portrait.findall('{http://www.w3.org/2000/svg}path'):
            paths.append(f'<path d="{escape(path.attrib["d"], quote=True)}" fill-opacity="{path.attrib.get("fill-opacity", "1")}" transform="{escape(path.attrib.get("transform", ""), quote=True)}"/>')
        body.append(f'<g fill="{fg}" transform="translate({portrait_x},{portrait_y}) scale({portrait_scale})">{"".join(paths)}</g>')
        rows = [(30, 'section', 'ahmad@eltobshy'),
            (50, 'OS', profile['OS']), (70, 'Location', 'Egypt'),
            (90, 'Role', 'BIM Developer'), (110, 'Coding.Since', '2020'),
            (130, 'IDE', profile['IDE']),
            (170, 'Language.Programming', 'C#, TypeScript, JavaScript'),
            (190, 'Language.Computer', 'HTML, CSS, SQL'),
            (210, 'Language.Real', profile['Languages.Spoken']),
            (250, 'Focus.Software', 'BIM process automation'),
            (270, 'Frameworks', '.NET, Node.js, Angular, React'),
            (310, 'section', 'Contact'), (330, 'Email.Personal', 'ahmadeltobshy@gmail.com'),
            (350, 'GitHub', '@AhmadEltobshy'), (450, 'section', 'GitHub Stats'),
            (470, 'Repos.Public', str(user['public_repos'])),
            (490, 'Stars / Followers', f"{sum(r['stargazers_count'] for r in repos if not r['fork'])} / {user['followers']}"),
            (510, 'Contributions.Year', f"{calendar['totalContributions']:,}")]
        for y, key, val in rows:
            if key == 'section':
                label = val if y == 30 else '- ' + val
                heading = label + ' -' + '—' * max(0, 57 - len(label) - 2) + '-'
                body.append(text(390, y, heading, fg, 16))
            elif key:
                dots = '.' * max(2, 54 - len(key) - len(val))
                label = f'<tspan fill="{fg}">.</tspan>'.join(f'<tspan fill="{accent}">{escape(part)}</tspan>' for part in key.split('.'))
                body.append(f'<text x="390" y="{y}" font-size="16"><tspan fill="{muted}">. </tspan>{label}<tspan fill="{fg}">:</tspan><tspan fill="{muted}"> {dots} </tspan><tspan fill="{value}">{escape(val)}</tspan></text>')
        card_svg = svg(985, 530, bg, body, 'Ahmad Eltobshy — BIM Developer')
        # The dark profile card is a user-edited SVG. Keep it verbatim so the
        # scheduled refresh never rewrites its custom layout or artwork.
        if theme == 'dark' and (ROOT / 'assets' / 'custom_dark_mode.svg').exists():
            (ROOT / 'dark_mode.svg').write_bytes((ROOT / 'assets' / 'custom_dark_mode.svg').read_bytes())
        else:
            (ROOT / f'{theme}_mode.svg').write_text(card_svg, encoding='utf-8')
        for name, label, detail in [('projects', 'Repositories', 'Explore my work ↗'), ('email', 'Get in touch', 'Send me an email ↗')]:
            elements = [text(24, 32, label, accent, 18, 'bold'), text(24, 58, detail, fg, 14), text(452, 46, '↗', muted, 24)]
            (ROOT / f'link_{name}_{theme}.svg').write_text(svg(502, 80, bg, elements, label), encoding='utf-8')
        weeks = calendar['weeks']
        pitch, left, top = 18, 32, 64
        width = max(1018, left * 2 + len(weeks) * pitch)
        board = [text(left, 31, 'CONTRIBUTIONS / LAST 12 MONTHS', accent, 15, 'bold'),
                 text(width - 250, 31, f"{calendar['totalContributions']:,} contributions", fg, 14)]
        level_names = ['NONE','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FOURTH_QUARTILE']
        for col, week in enumerate(weeks):
            for day in week['contributionDays']:
                import datetime
                row = (datetime.date.fromisoformat(day['date']).weekday() + 1) % 7
                x, y = left + col * pitch, top + row * pitch
                level = level_names.index(day['contributionLevel'])
                step = row * len(weeks) + (col if row % 2 == 0 else len(weeks) - 1 - col)
                eaten = max(0.001, step / (7 * len(weeks)))
                board.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="3" fill="{levels[level]}"><title>{day["date"]}: {day["contributionCount"]} contributions</title><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{eaten:.5f};{eaten+0.001:.5f};1" dur="30s" repeatCount="indefinite"/></rect>')
        # A continuous serpentine route sweeps every contribution week.
        points = []
        for row in range(7):
            cols = range(len(weeks)) if row % 2 == 0 else reversed(range(len(weeks)))
            points.extend((left + col * pitch + 6, top + row * pitch + 6) for col in cols)
        path = 'M ' + ' L '.join(f'{x},{y}' for x, y in points)
        board.append(f'<g transform="translate({points[0][0]},{points[0][1]})"><g><circle r="8" fill="#f5c842"/><path d="M 0,0 L 9,-5 L 9,5 Z" fill="{bg}"><animateTransform attributeName="transform" type="scale" values="1,1;1,0.1;1,1" dur="0.24s" repeatCount="indefinite"/></path><animateMotion dur="30s" repeatCount="indefinite" rotate="auto" path="M 0,0 ' + ' '.join(f'L {x-points[0][0]},{y-points[0][1]}' for x,y in points[1:]) + '"/></g></g>')
        board.append(text(left, 222, 'One contribution at a time.', muted, 13))
        (ROOT / f'pacman_{theme}.svg').write_text(svg(width, 245, bg, board, 'Pac-Man sweeping Ahmad’s real GitHub contribution graph'), encoding='utf-8')

if __name__ == '__main__':
    build()
