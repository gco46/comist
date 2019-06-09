class CssSelectors(object):
    # 一覧ページ -> 漫画の詳細ページ
    to_detail_page = 'div.article-body-inner a::attr(href)'
    # 一覧ページ -> 次の一覧ページ
    to_next_page = 'div.wp-pagenavi a.nextpostslink::attr(href)'
    # 詳細ページ -> 画像url
    to_images = 'section.entry-content img::attr(src)'
    # 詳細ページ -> タグ情報
    to_tags = 'div.article-tags ul li a::text'
    # 詳細ページ -> カテゴリ情報
    to_category = '.post-categories li a::text'
    # 詳細ページ -> 連作url
    to_continuous = 'div.box_rensaku li a::attr(href)'
