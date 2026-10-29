import os
import re
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# class="..." 属性 と JS の className: '...' 文字列からクラストークンを収集する
TOKEN_PATTERNS = [
    re.compile(r'class="([^"]+)"'),
    re.compile(r"className:\s*'([^']+)'"),
]

# トークンとして扱う文字(utility クラス・バリアント・opacity 修飾など)
TOKEN_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9./:-]*$")

# CSS 側のセレクタ抽出(.hover\:text-accent / .w-2\.5 のようなエスケープ込み)
# 継続部分に未エスケープの ':' を含めない(:hover などの疑似クラスを巻き込まないため)
SELECTOR_RE = re.compile(r"\.([a-zA-Z][a-zA-Z0-9-]*(?:\\[:/.][a-zA-Z0-9./-]+)*)")

COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)


def read(path):
    with open(os.path.join(BASE_DIR, path), encoding="utf-8") as f:
        return f.read()


def used_tokens(html):
    tokens = set()
    for pattern in TOKEN_PATTERNS:
        for m in pattern.finditer(html):
            for token in m.group(1).split():
                if TOKEN_RE.match(token):
                    tokens.add(token)
    return tokens


def defined_tokens(css):
    tokens = set()
    for m in SELECTOR_RE.finditer(COMMENT_RE.sub("", css)):
        tokens.add(
            m.group(1).replace("\\:", ":").replace("\\/", "/").replace("\\.", ".")
        )
    return tokens


class TestTailwindCdnRemoved(unittest.TestCase):
    def test_no_cdn_reference(self):
        html = read("index.html")
        self.assertNotIn("cdn.tailwindcss.com", html, "Tailwind CDN が残っている")
        self.assertNotIn("tailwind.config", html, "tailwind.config が残っている")
        self.assertIn('href="styles.css"', html, "styles.css が読み込まれていない")


class TestCssCoverage(unittest.TestCase):
    def setUp(self):
        html = read("index.html")
        self.used = used_tokens(html)
        # styles.css に加えて index.html 内 <style> のカスタムクラスも定義扱いにする
        self.defined_in_css = defined_tokens(read("styles.css"))
        self.defined = set(self.defined_in_css)
        for m in STYLE_RE.finditer(html):
            self.defined |= defined_tokens(m.group(1))

    def test_tokens_collected(self):
        self.assertGreater(len(self.used), 40, "クラスの収集に失敗した可能性")

    def test_all_used_classes_are_defined(self):
        missing = sorted(self.used - self.defined)
        self.assertEqual(missing, [], f"定義がないクラス: {missing}")

    def test_no_unused_definitions_in_styles_css(self):
        # index.html 内 <style> の予備クラス(delay-100 など)は対象外
        unused = sorted(self.defined_in_css - self.used)
        self.assertEqual(unused, [], f"styles.css に使用されていない定義: {unused}")


if __name__ == "__main__":
    unittest.main()
