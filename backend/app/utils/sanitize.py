import nh3

# 富文本白名单：入库前服务端清洗，前端展示时无需再信任原始 HTML
ALLOWED_TAGS = {
    "p", "br", "hr", "strong", "em", "u", "s", "sub", "sup",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "code", "pre",
    "a", "img", "span", "div",
    "table", "thead", "tbody", "tr", "th", "td",
}

ALLOWED_ATTRIBUTES = {
    # rel 由 nh3 的 link_rel 机制自动管理(默认加 noopener noreferrer)，不可重复放行
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "width", "height"},
    "span": {"style"},  # 常见编辑器行内样式；nh3 只保留纯 CSS 属性
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize_rich_text(html: str) -> str:
    """白名单清洗富文本：剥离 script/事件属性/危险协议。"""
    if not html:
        return ""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
    )
