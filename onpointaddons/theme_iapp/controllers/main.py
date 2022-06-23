# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.website.controllers.main import QueryURL
import werkzeug
from odoo.addons.http_routing.models.ir_http import slug, unslug

from odoo import http,fields
from odoo.http import request
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.addons.website_form.controllers.main import WebsiteForm
import json

class WebsiteForm(WebsiteForm):
    
    # Check and insert values from the form on the model <model>
    @http.route('/contact_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'website.contact.info' and not request.params.get('state_id'):
            geoip_country_code = request.session.get('geoip', {}).get('country_code')
            geoip_state_code = request.session.get('geoip', {}).get('region')
            if geoip_country_code and geoip_state_code:
                State = request.env['res.country.state']
                request.params['state_id'] = State.search([('code', '=', geoip_state_code), ('country_id.code', '=', geoip_country_code)]).id

        return super(WebsiteForm, self).website_form(model_name, **kwargs)


class WebsiteBlog(WebsiteBlog):
    
    # override blog method 
    @http.route([
        '/blog',
        '/blog/page/<int:page>',
        '/blog/tag/<string:tag>',
        '/blog/tag/<string:tag>/page/<int:page>',
        '''/blog/<model("blog.blog", "[('website_id', 'in', (False, current_website_id))]"):blog>''',
        '''/blog/<model("blog.blog"):blog>/page/<int:page>''',
        '''/blog/<model("blog.blog"):blog>/tag/<string:tag>''',
        '''/blog/<model("blog.blog"):blog>/tag/<string:tag>/page/<int:page>''',
         '''/blog/search_content''',
    ], type='http', auth="public", website=True)
    def blog(self, blog=None, tag=None, page=1, **opt):
        Blog = request.env['blog.blog']
        if blog and not blog.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()

        blogs = Blog.search(request.website.website_domain(), order="create_date asc, id asc")

        if not blog and len(blogs) == 1:
            return werkzeug.utils.redirect('/blog/%s' % slug(blogs[0]), code=302)

        date_begin, date_end, state = opt.get('date_begin'), opt.get('date_end'), opt.get('state')
        BlogPost = request.env['blog.post']

        # prepare domain
        domain = request.website.website_domain()

        if blog:
            domain += [('blog_id', '=', blog.id)]

        if date_begin and date_end:
            domain += [("post_date", ">=", date_begin), ("post_date", "<=", date_end)]
 
        active_tag_ids = tag and [unslug(tag)[1] for tag in tag.split(',')] or []
        if active_tag_ids:
            fixed_tag_slug = ",".join(slug(t) for t in request.env['blog.tag'].browse(active_tag_ids))
            if fixed_tag_slug != tag:
                return request.redirect(request.httprequest.full_path.replace("/tag/%s/" % tag, "/tag/%s/" % fixed_tag_slug, 1), 301)

            domain += [('tag_ids', 'in', active_tag_ids)]

        if request.env.user.has_group('website.group_website_designer'):
            count_domain = domain + [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            published_count = BlogPost.search_count(count_domain)
            unpublished_count = BlogPost.search_count(domain) - published_count

            if state == "published":
                domain += [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            elif state == "unpublished":
                domain += ['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())]
        else:
            domain += [("post_date", "<=", fields.Datetime.now())]
        blog_url = QueryURL('', ['blog', 'tag'], blog=blog, tag=tag, date_begin=date_begin, date_end=date_end)    
        search_strings = opt.get('search', None)

        blog_posts = BlogPost.search([('name', 'ilike', search_strings)],
                                      offset=(page - 1) * self._blog_post_per_page,
                                      limit=self._blog_post_per_page) if search_strings \
                                      else BlogPost.search(domain,
                                                           order="post_date desc")

        pager = request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            total=len(blog_posts),
            page=page,
            step=self._blog_post_per_page,
            url_args=opt,
        )    
        pager_begin = (page - 1) * self._blog_post_per_page
        pager_end = page * self._blog_post_per_page
        blog_posts = blog_posts[pager_begin:pager_end]
        
        use_cover = request.website.viewref('website_blog.opt_blog_cover_post').active
        fullwidth_cover = request.website.viewref('website_blog.opt_blog_cover_post_fullwidth_design').active

        # if blog, we show blog title, if use_cover and not fullwidth_cover we need pager + latest always
        offset = (page - 1) * self._blog_post_per_page
        first_post = BlogPost
        if not blog:
            first_post = BlogPost.search(domain + [('website_published', '=', True)], order="post_date desc, id asc", limit=1)
            if use_cover and not fullwidth_cover:
                offset += 1
        all_tags = blog and blogs.all_tags()[blog.id] or blogs.all_tags(join=True)
        tag_category = sorted(all_tags.mapped('category_id'), key=lambda category: category.name.upper())
        other_tags = sorted(all_tags.filtered(lambda x: not x.category_id), key=lambda tag: tag.name.upper())

        # for performance prefetch the first post with the others
        values = {
            'date_begin': date_begin,
            'date_end': date_end,
            'first_post': first_post.with_prefetch(blog_posts.ids) if not search_strings else None,
            'other_tags': other_tags,
            'tag_category': tag_category,
            'nav_list': self.nav_list(blog),
            'tags_list': self.tags_list,
            'pager': pager,
            'posts': blog_posts,
#             'tag': tags,
            'active_tag_ids': active_tag_ids,
            'domain': domain,
            'state_info': state and {"state": state, "published": published_count, "unpublished": unpublished_count},
            'blogs': blogs,
            'blog': blog,
            'blog_url': blog_url,
        }
        return request.render("website_blog.blog_post_short", values)
    
    # blog search suggestion
    @http.route('/blog/search', csrf=False, type="http", methods=['POST', 'GET'], auth="public", website=True)
    def search_contents(self, **kw):
        """
            Searches blog according to the category selected on front,
            :param kw: dict contains the category and search key
            :return: Dict with params as name, res_id, value
        """
        strings = '%' + kw.get('name') + '%'
        try:
            domain = [('website_published', '=', True)] 
            blog = request.env['blog.post'].search(domain)
            sql = """select id as res_id, name as name, name as value from blog_post where name ILIKE '{}'"""
            extra_query = ''
            limit = " limit 15"
            query = sql+extra_query+limit
            request.cr.execute(query.format(strings, tuple(blog and blog.ids)))
            name = request.cr.dictfetchall()
        except:
            name = {'name': 'None', 'value': 'None'}
        return json.dumps(name)
    
    # Overrride blog post method    
    @http.route([
        '''/blog/<model("blog.blog", "[('website_id', 'in', (False, current_website_id))]"):blog>/post/<model("blog.post", "[('blog_id','=',blog[0])]"):blog_post>''',
    ], type='http', auth="public", website=True,csrf=False)
    def blog_post(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):
        """ Prepare all values to display the blog.

        :return dict values: values for the templates, containing

         - 'blog_post': browse of the current post
         - 'blog': browse of the current blog
         - 'blogs': list of browse records of blogs
         - 'tag': current tag, if tag_id in parameters
         - 'tags': all tags, for tag-based navigation
         - 'pager': a pager on the comments
         - 'nav_list': a dict [year][month] for archives navigation
         - 'next_post': next blog post, to direct the user towards the next interesting post
        """
        # create comment code
        if post:
            author_id = request.env.user.partner_id.id if request.env.user.partner_id else False
            partner = request.env['res.partner'].sudo().browse(author_id)
            email_from = partner.email_formatted if partner.email else None
            model_name = blog_post._name
            message = request.env['mail.message'].sudo().create({
            'subject': post['subject'],
            'body': post['message'],
             'model':blog_post._name,
#             'subtype_id': self.ref('mail.mt_comment'),
             'message_type': 'comment',
             'email_id' : post['email'],
             'name' : post['name'],
            'res_id' : blog_post.id,
             'parent_id' :blog_post.id,
            'author_id' : author_id,
            'email_from' :email_from,
            })
            
        if not blog.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()

        BlogPost = request.env['blog.post']
        date_begin, date_end = post.get('date_begin'), post.get('date_end')

        pager_url = "/blogpost/%s" % blog_post.id

        pager = request.website.pager(
            url=pager_url,
            total=len(blog_post.website_message_ids),
            page=page,
            step=self._post_comment_per_page,
            scope=7
        )
        pager_begin = (page - 1) * self._post_comment_per_page
        pager_end = page * self._post_comment_per_page
        comments = blog_post.website_message_ids[pager_begin:pager_end]
        total_comment = len(blog_post.website_message_ids)
        domain = request.website.website_domain()
        blogs = blog.search(domain, order="create_date, id asc")

        tag = None
        if tag_id:
            tag = request.env['blog.tag'].browse(int(tag_id))
        blog_url = QueryURL('', ['blog', 'tag'], blog=blog_post.blog_id, tag=tag, date_begin=date_begin, date_end=date_end)

        if not blog_post.blog_id.id == blog.id:
            return request.redirect("/blog/%s/post/%s" % (slug(blog_post.blog_id), slug(blog_post)), code=301)

        tags = request.env['blog.tag'].search([])

        # Find next Post
        blog_post_domain = [('blog_id', '=', blog.id)]
        if not request.env.user.has_group('website.group_website_designer'):
            blog_post_domain += [('post_date', '<=', fields.Datetime.now())]

        all_post = BlogPost.search(blog_post_domain)

        if blog_post not in all_post:
            return request.redirect("/blog/%s" % (slug(blog_post.blog_id)))

        # should always return at least the current post
        all_post_ids = all_post.ids
        current_blog_post_index = all_post_ids.index(blog_post.id)
        nb_posts = len(all_post_ids)
        next_post_id = all_post_ids[(current_blog_post_index + 1) % nb_posts] if nb_posts > 1 else None
        next_post = next_post_id and BlogPost.browse(next_post_id) or False

        values = {
            'tags': tags,
            'tag': tag,
            'blog': blog,
            'blog_post': blog_post,
            'blogs': blogs,
            'main_object': blog_post,
            'nav_list': self.nav_list(blog),
            'enable_editor': enable_editor,
            'next_post': next_post,
            'date': date_begin,
            'blog_url': blog_url,
            'pager': pager,
            'comments': comments,
            'total_comment' : total_comment,
        }
        response = request.render("website_blog.blog_post_complete", values)

        request.session[request.session.sid] = request.session.get(request.session.sid, [])
        if not (blog_post.id in request.session[request.session.sid]):
            request.session[request.session.sid].append(blog_post.id)
            # Increase counter
            blog_post.sudo().write({
                'visits': blog_post.visits + 1,
            })
        return response
 