title: 在Rails中实现markdown解析
date: 2014-11-13 16:39:34
tags: rails
---

首先，安装gem
```
gem 'redcarpet'
```
然后在app/helpers/application_helper.rb添加如下代码：
```
def markdown(text)
    render_options = {
        filter_html:     false,
        hard_wrap:       true, 
        link_attributes: { rel: 'nofollow' }
    }
    renderer = Redcarpet::Render::HTML.new(render_options)
    extensions = {
            #will parse links without need of enclosing them
            autolink:           true,
            fenced_code_blocks: true,
            # will ignore standard require for empty lines surrounding HTML blocks
            lax_spacing:        true,
            # will not generate emphasis inside of words, for example no_emph_no
            no_intra_emphasis:  true,
            # will parse strikethrough from ~~, for example: ~~bad~~
            strikethrough:      true,
            # will parse superscript after ^, you can wrap superscript in () 
            superscript:        true
            # will require a space after # in defining headers
            # space_after_headers: true
        }
    Redcarpet::Markdown.new(renderer, extensions).render(text).html_safe
end
```
在view中:
` <%= markdown @content %> `

在controller中：
```
class ApplicationController < ActionController::Base
    include ApplicationHelper
end
```