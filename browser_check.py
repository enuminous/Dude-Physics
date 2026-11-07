#!/usr/bin/env python3
"""Optional offline browser checks. Requires Playwright and a Chromium executable.

Not required by verify.py or the dependency-free offline page.
Screenshots, if requested, are written only to the directory you supply.
"""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', required=True, help='Path to Chromium executable')
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser, headless=True, args=['--no-sandbox'])
        print('Browser:', browser.version)
        for width, height in [(1440, 1000), (390, 844)]:
            page = browser.new_page(viewport={'width': width, 'height': height}, reduced_motion='reduce')
            errors, network = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: network.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
            page.goto((ROOT / 'index.html').as_uri(), wait_until='load')
            assert page.locator('.artifact:visible').count() == 72
            assert page.locator('#room-image').evaluate('(img) => img.complete && img.naturalWidth > 0')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow on index'
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / f'index-{width}.png'))
            page.locator('[data-room="original"]').click()
            page.wait_for_function("document.querySelector('#room-image').complete && document.querySelector('#room-image').naturalWidth > 0 && document.querySelector('#room-image').src.endsWith('room-original.jpeg')")
            assert 'original empty room' in page.locator('#room-image').get_attribute('alt')
            page.locator('[data-room="generated"]').click()
            assert page.locator('[data-room="generated"]').get_attribute('aria-pressed') == 'true'
            page.locator('#search').fill('music guitar')
            assert page.locator('.artifact:visible').count() == 2
            page.locator('#search').press('Enter')
            assert page.locator('.artifact:visible').count() == 2
            page.locator('#category').select_option('Research')
            assert page.locator('#empty-state').is_visible()
            page.locator('button[type="reset"]').click()
            page.wait_for_function("document.querySelector('#result-count').textContent === '72 of 72 entries'")
            page.locator('#category').select_option('Zoo')
            page.locator('#reading').select_option('interpretive')
            expected = len([x for x in json.loads((ROOT/'inventory.json').read_text()) if x['category']=='Zoo' and x['reading']=='interpretive'])
            assert page.locator('.artifact:visible').count() == expected
            page.locator('#find-rug').click()
            assert page.locator('.artifact:visible').count() == 1
            assert page.locator('#artifact-66').is_visible()
            for key, label in [('physics','NOT ESTABLISHED'), ('satire','SATIRE'), ('composition','AESTHETIC INTERPRETATION')]:
                page.locator(f'[data-claim="{key}"]').click()
                assert page.locator('#claim-result strong').inner_text() == label
                assert page.locator(f'[data-claim="{key}"]').get_attribute('aria-pressed') == 'true'
            if args.screenshots:
                page.locator('#rug').screenshot(path=str(args.screenshots / f'rug-{width}.png'))
            page.goto((ROOT / 'reading.html').as_uri(), wait_until='load')
            assert page.locator('.chapter').count() == 9
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow in reader'
            page.locator('.contents a[href="#rug-theory"]').click()
            assert page.url.endswith('#rug-theory')
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / f'reader-{width}.png'))
            assert not errors, errors
            assert not network, network
            page.close()
            print(f'PASS: {width}×{height}: local-file load, images, catalog, filters, reset, rug, claim labels, reader, no overflow, no page errors, no HTTP requests')
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.goto((ROOT / 'index.html').as_uri(), wait_until='load')
        assert page.locator('.artifact').count() == 72
        assert page.locator('noscript').is_visible()
        context.close()
        print('PASS: JavaScript-disabled static catalog and fallback notice')
        browser.close()


if __name__ == '__main__':
    main()
