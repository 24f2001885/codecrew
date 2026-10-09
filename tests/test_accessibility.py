from html.parser import HTMLParser
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project


class A11yParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.interactive_empty_text = []
        self.inputs = []
        self.label_fors = set()
        self.title = ""
        self.in_title = False
        self.has_skip_link = False
        self.has_main_content = False
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "img":
            self.images.append(attr_dict)
        elif tag in ("input", "textarea", "select"):
            if attr_dict.get("type") not in ("hidden", "submit", "image"):
                self.inputs.append(attr_dict)
        elif tag == "label":
            if "for" in attr_dict:
                self.label_fors.add(attr_dict["for"])
        elif tag in ("a", "button"):
            if tag == "a" and "skip-link" in attr_dict.get("class", ""):
                self.has_skip_link = True
            self.tag_stack.append((tag, attr_dict, []))
        elif tag == "main":
            if attr_dict.get("id") == "main-content":
                self.has_main_content = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("a", "button") and self.tag_stack and self.tag_stack[-1][0] == tag:
            item = self.tag_stack.pop()
            text = "".join(item[2]).strip()
            attrs = item[1]
            if not text:
                # Text is empty — must have aria-label, aria-labelledby, or title
                self.interactive_empty_text.append((tag, attrs))

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.tag_stack:
            self.tag_stack[-1][2].append(data)


def parse_page(html_content):
    parser = A11yParser()
    parser.feed(html_content)
    return parser


def test_public_pages_accessibility_and_skip_link(app, client):
    # Seed a sample group so group detail exists
    with app.app_context():
        g = Group(name="Apex Collective", slug="apex-collective", tagline="High velocity engineering", description="Detailed squad bio.")
        db.session.add(g)
        db.session.commit()

    public_urls = ["/", "/groups", "/group/apex-collective", "/members", "/request-project"]
    titles = set()

    for url in public_urls:
        resp = client.get(url)
        assert resp.status_code == 200, f"Failed on {url}"
        html = resp.data.decode("utf-8")
        parsed = parse_page(html)

        # 1. Skip link and main content container
        assert parsed.has_skip_link, f"Skip link missing on {url}"
        assert parsed.has_main_content, f"<main id='main-content'> missing on {url}"

        # 2. Every <img> has an alt attribute
        for img in parsed.images:
            assert "alt" in img, f"Image missing alt attribute on {url}: {img}"
            # Non-empty unless explicitly whitelisted decorative
            alt = img["alt"]
            is_decorative = "decorative" in img.get("class", "")
            if not is_decorative:
                assert len(alt.strip()) > 0, f"Image has empty alt on {url}: {img}"

        # 3. Unique titles across page types
        clean_title = parsed.title.strip()
        assert len(clean_title) > 0, f"Page title missing on {url}"
        assert clean_title not in titles, f"Duplicate page title '{clean_title}' on {url}"
        titles.add(clean_title)

        # 4. Icon-only buttons or links have aria-label
        for tag, attrs in parsed.interactive_empty_text:
            has_aria = "aria-label" in attrs or "aria-labelledby" in attrs or "title" in attrs
            assert has_aria, f"Interactive {tag} without text has no aria-label on {url}: {attrs}"


def test_admin_login_accessibility(client):
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    parsed = parse_page(html)
    for inp in parsed.inputs:
        input_id = inp.get("id")
        has_label = input_id and input_id in parsed.label_fors
        has_aria = "aria-label" in inp or "aria-labelledby" in inp or "placeholder" in inp
        assert has_label or has_aria, f"Form input missing label on /admin/login: {inp}"


def test_admin_pages_accessibility(logged_in_client):
    admin_urls = ["/admin/groups", "/admin/settings"]
    for url in admin_urls:
        resp = logged_in_client.get(url)
        assert resp.status_code == 200, f"Failed on {url}"
        html = resp.data.decode("utf-8")
        parsed = parse_page(html)

        # Every <img> has an alt attribute
        for img in parsed.images:
            assert "alt" in img, f"Image missing alt on {url}: {img}"

        # Every form control has an associated label or aria-label
        for inp in parsed.inputs:
            input_id = inp.get("id")
            has_label = input_id and input_id in parsed.label_fors
            has_aria = "aria-label" in inp or "aria-labelledby" in inp or "placeholder" in inp
            assert has_label or has_aria, f"Form input missing label on {url}: {inp}"

