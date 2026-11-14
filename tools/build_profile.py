"""Build original, self-contained SVG artwork for Ahmad's GitHub README."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from html import escape

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
<style>text {{font-family:Consolas,Menlo,monospace;white-space:pre}}</style>
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
    portrait = (ROOT / 'assets' / 'portrait.txt').read_text().splitlines()
    portrait_size = min(11, 408 / (max(map(len, portrait), default=1) * 0.61), 452 / (max(1, len(portrait)) * 1.5))
    portrait_step = portrait_size * 1.5
    portrait_top = (565 - (len(portrait) - 1) * portrait_step) / 2
    profile = json.loads((ROOT / 'assets' / 'profile.json').read_text(encoding='utf-8'))
    for theme, bg, fg, muted, accent, value, levels in [
        ('dark', '#161b22', '#c9d1d9', '#778395', '#f78c35', '#a5d6ff', ['#242d38','#0e4429','#006d32','#26a641','#39d353']),
        ('light', '#f6f8fa', '#24292f', '#6e7781', '#b64b08', '#0550ae', ['#e6e9ed','#9be9a8','#40c463','#30a14e','#216e39'])]:
        body = []
        for i, line in enumerate(portrait):
            body.append(text(20, portrait_top + i * portrait_step, line, muted, portrait_size))
        rows = [('section', 'ahmad@eltobshy')]
        rows += [(k, profile[k]) for k in ['OS', 'Workplace', 'IDE'] if profile.get(k)]
        rows += [('Role', 'BIM Developer'), ('Location', 'Egypt'), ('', ''),
            ('Languages.Programming', 'C#, TypeScript, JavaScript'),
            ('Languages.Computer', 'HTML, CSS, SQL')]
        if profile.get('Languages.Spoken'):
            rows.append(('Languages.Spoken', profile['Languages.Spoken']))
        rows += [('', ''), ('Focus', 'BIM process automation'),
            ('Frameworks', '.NET, Node.js, Angular, React'), ('', ''),
            ('section', 'Contact'), ('Email.Personal', 'ahmadeltobshy@gmail.com'),
            ('GitHub', '@AhmadEltobshy'), ('', ''), ('section', 'GitHub Stats'),
            ('Public repos', str(user['public_repos'])),
            ('Stars / Followers', f"{sum(r['stargazers_count'] for r in repos if not r['fork'])} / {user['followers']}"),
            ('Contributions.Year', f"{calendar['totalContributions']:,}")]
        step = min(23, 510 / max(1, len(rows) - 1))
        for i, (key, val) in enumerate(rows):
            y = 31 + i * step
            if key == 'section':
                heading = val + ' ' + '─' * max(0, 65 - len(val))
                body.append(text(432, y, heading, fg, 14))
            elif key:
                dots = '.' * max(2, 63 - len(key) - len(val))
                body.append(f'<text x="432" y="{y}" font-size="14"><tspan fill="{muted}">. </tspan><tspan fill="{accent}">{escape(key)}</tspan><tspan fill="{muted}">: {dots} </tspan><tspan fill="{value}">{escape(val)}</tspan></text>')
        (ROOT / f'{theme}_mode.svg').write_text(svg(1018, 565, bg, body, 'Ahmad Eltobshy — BIM Developer'), encoding='utf-8')
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
