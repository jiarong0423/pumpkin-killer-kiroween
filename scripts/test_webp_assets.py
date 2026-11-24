import json, os, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


class WebpAssets(unittest.TestCase):
    def test_every_webp_matches_its_png(self):
        r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "make_webp_assets.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_asset_url_maps_only_listed_pictures_and_only_with_webp_support(self):
        js = (
            "global.self = global; global.document = undefined; require(%r);"
            "const off = assetUrl('assets/env/bg_graveyard.png');"
            "global.document = { createElement: () => ({ toDataURL: () => 'data:image/webp;base64,xx' }) };"
            "delete require.cache[require.resolve(%r)]; require(%r);"
            "console.log(JSON.stringify([off, assetUrl('assets/env/bg_graveyard.png'), assetUrl('./assets/env/bg_graveyard.png'), assetUrl('assets/ui/not_listed.png'), assetUrl(5)]));"
        ) % ((os.path.join(ROOT, "js", "webp_manifest.js"),) * 3)
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        off, on, dotted, unlisted, number = json.loads(r.stdout)
        self.assertEqual(off, "assets/env/bg_graveyard.png")
        self.assertEqual(on, "assets/env/bg_graveyard.webp")
        self.assertEqual(dotted, "assets/env/bg_graveyard.webp")
        self.assertEqual(unlisted, "assets/ui/not_listed.png")
        self.assertEqual(number, 5)

    def test_page_and_service_worker_use_the_manifest(self):
        page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        sw = open(os.path.join(ROOT, "sw.js"), encoding="utf-8").read()
        self.assertIn('<script src="js/webp_manifest.js"></script>', page)
        self.assertGreaterEqual(page.count("assetUrl("), 5)
        self.assertIn('importScripts("js/webp_manifest.js")', sw)


if __name__ == "__main__":
    unittest.main()
