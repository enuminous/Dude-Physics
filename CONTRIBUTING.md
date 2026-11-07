# Maintaining the room

1. Edit `inventory.json` for catalog text. Preserve IDs 1–72 when describing this
   historical inventory. Identify any future expanded catalog separately.
2. Edit the individual Markdown essays and `index.template.html`, `styles.css`
   or `app.js` as appropriate. `reading.html`, `index.html`, `INVENTORY.md` and
   `inventory.js` are generated.
3. Run `python3 build.py` to regenerate the four outputs.
4. Run `node test.cjs` for the catalog filtering and editorial claim behavior.
5. Run `python3 release.py` to check generated files, refresh `SHA256SUMS`, run
   `verify.py`, and create a new flat-root ZIP in the parent directory. This
   overwrites that ZIP if it already exists. Use `--output /path/name.zip` for a
   different destination.

`python3 verify.py` checks the current release hashes when present. After an
intentional edit, those old hashes will correctly fail until refreshed by
`release.py`. Refreshing a hash does not validate a scientific claim.

The optional `browser_check.py` requires Playwright and a working Chromium
executable. Run `python3 browser_check.py --browser /path/to/chromium` in a
compatible environment. It tests local-file loading, desktop/mobile viewports,
image switching, catalog controls, claim labels, the reader and the no-JavaScript
fallback. A successful run is still not a complete accessibility audit.

Keep the original image files unchanged when maintaining this edition. If you
make a new edition with edited images, preserve the originals, document the new
provenance and update the corresponding manifest intentionally.

Every new scientific claim needs an evidence entry. Every fictional law needs a
satire label. The rug does not grant exceptions.
