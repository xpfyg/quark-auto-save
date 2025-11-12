---
title: {{ title }}
description: {{ description }}
keywords: {{ keywords }}
date: {{ generate_time }}
updated: {{ update_time }}
category: {{ category2 }}
tags:
  - {{ category2 }}
  - {{ drive_type }}
  - 网盘资源
author: {{ site_name }}
robots: index, follow
canonical: {{ page_url }}
og:title: {{ title }}
og:description: {{ description }}
og:type: article
og:url: {{ page_url }}
og:site_name: {{ site_name }}
{% if tmdb and tmdb.poster_url %}
og:image: {{ tmdb.poster_url }}
og:image:width: 500
og:image:height: 750
og:image:alt: {{ tmdb.title }}海报
{% endif %}
twitter:card: summary_large_image
twitter:title: {{ title }}
twitter:description: {{ description }}
{% if tmdb and tmdb.poster_url %}
twitter:image: {{ tmdb.poster_url }}
{% endif %}
---

# {{ title }}

> 📅 更新时间：{{ update_time }}
> 📁 分类：{{ category1 }} / {{ category2 }}
> ☁️ 网盘：{{ drive_type }}
> 👁️ 浏览：{{ view_count }} 次 | 👆 点击：{{ share_count }} 次

## 📋 资源信息

{% if tmdb %}
### 🎬 影视详情

- **片名**：{{ tmdb.title }}
- **年份**：{{ tmdb.year_released or '未知' }}
- **类型**：{{ tmdb.category or category2 }}
{% if tmdb.vote_average %}
- **评分**：⭐ {{ tmdb.vote_average }}/10
{% endif %}
- **简介**：{{ tmdb.description or '暂无简介' }}

{% if tmdb.poster_url %}
![{{ tmdb.title }}]({{ tmdb.poster_url }} "{{ tmdb.title }}海报")
{% endif %}

{% endif %}

## 📥 获取资源

**资源名称**：{{ drama_name }}
{% if alias and alias != drama_name %}
**别名**：{{ alias }}
{% endif %}
{% if size %}
**文件大小**：{{ size }}
{% endif %}

### 🔗 下载链接

<div class="download-button">

[**🔗 立即获取《{{ drama_name }}》资源**]({{ share_link }})

</div>

> ⚠️ **使用说明**：
> 1. 点击上方按钮跳转到网盘分享页面
> 2. 本站无需关注或注册，完全免费
> 3. 如遇到链接失效，请联系站长更新

## 🔍 相关推荐

{% if related_resources %}
{% for related in related_resources %}
- [{{ related.title }}]({{ related.url }}) - {{ related.category }}
{% endfor %}
{% else %}
暂无相关推荐
{% endif %}

## 📊 资源标签

#{{ category2 }} #{{ drive_type }} #网盘资源 #在线观看 #免费下载

---

<small>
📝 页面ID: {{ resource_id }}
⏰ 生成时间: {{ generate_time }}
🔄 最后更新: {{ update_time }}
</small>

<!-- 面包屑导航结构化数据 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "首页",
      "item": "{{ site_url }}"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ category1 }}",
      "item": "{{ site_url }}/category/{{ category1 }}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{ category2 }}",
      "item": "{{ site_url }}/category/{{ category2 }}"
    },
    {
      "@type": "ListItem",
      "position": 4,
      "name": "{{ drama_name }}",
      "item": "{{ page_url }}"
    }
  ]
}
</script>

<!-- 主要内容结构化数据 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "{{ schema_type }}",
  "name": "{{ drama_name }}",
  "headline": "{{ title }}",
  "description": "{{ description }}",
  {% if tmdb %}
  {% if tmdb.poster_url %}
  "image": {
    "@type": "ImageObject",
    "url": "{{ tmdb.poster_url }}",
    "width": 500,
    "height": 750
  },
  {% endif %}
  {% if schema_type == 'Movie' %}
  "datePublished": "{{ tmdb.year_released }}-01-01",
  {% endif %}
  {% if schema_type == 'TVSeries' %}
  "datePublished": "{{ tmdb.year_released }}-01-01",
  {% endif %}
  {% if tmdb.vote_average %}
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "{{ tmdb.vote_average }}",
    "bestRating": "10",
    "worstRating": "0",
    "ratingCount": "{{ rating_count | default(100) }}"
  },
  {% endif %}
  "genre": "{{ tmdb.category or category2 }}",
  {% endif %}
  "url": "{{ page_url }}",
  "inLanguage": "zh-CN",
  "dateModified": "{{ update_time }}",
  "dateCreated": "{{ generate_time }}",
  "author": {
    "@type": "Organization",
    "name": "{{ site_name }}",
    "url": "{{ site_url }}"
  },
  "publisher": {
    "@type": "Organization",
    "name": "{{ site_name }}",
    "url": "{{ site_url }}"
  },
  "provider": {
    "@type": "Organization",
    "name": "{{ site_name }}"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "CNY",
    "availability": "https://schema.org/InStock",
    "priceValidUntil": "2099-12-31",
    "url": "{{ share_link }}"
  },
  "potentialAction": {
    "@type": "WatchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "{{ share_link }}",
      "actionPlatform": [
        "http://schema.org/DesktopWebPlatform",
        "http://schema.org/MobileWebPlatform"
      ]
    }
  },
  "interactionStatistic": [
    {
      "@type": "InteractionCounter",
      "interactionType": "https://schema.org/ViewAction",
      "userInteractionCount": {{ view_count }}
    },
    {
      "@type": "InteractionCounter",
      "interactionType": "https://schema.org/ShareAction",
      "userInteractionCount": {{ share_count }}
    }
  ]
}
</script>

<!-- 网站信息结构化数据 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "{{ site_name }}",
  "url": "{{ site_url }}",
  "description": "免费网盘资源分享平台，提供{{ category2 }}等各类资源",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "{{ site_url }}/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
</script>

<!-- 文章/内容结构化数据 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{ title }}",
  "description": "{{ description }}",
  {% if tmdb and tmdb.poster_url %}
  "image": "{{ tmdb.poster_url }}",
  {% endif %}
  "datePublished": "{{ generate_time }}",
  "dateModified": "{{ update_time }}",
  "author": {
    "@type": "Organization",
    "name": "{{ site_name }}"
  },
  "publisher": {
    "@type": "Organization",
    "name": "{{ site_name }}",
    "url": "{{ site_url }}"
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "{{ page_url }}"
  },
  "keywords": "{{ keywords }}",
  "articleSection": "{{ category2 }}",
  "wordCount": {{ word_count | default(500) }}
}
</script>
