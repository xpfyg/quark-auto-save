# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from db import db


class CloudResource(db.Model):
    '''
    网盘资源库表
    '''
    __tablename__ = 'cloud_resource'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    drama_name = db.Column(db.String(255), nullable=False, default='', comment='剧名')
    alias = db.Column(db.String(200), nullable=False, default='', comment='别名')
    category1 = db.Column(db.String(100), nullable=False, default='', comment='分类1,影视资源,学习资料')
    category2 = db.Column(db.String(100), comment='分类2（如电影、电视剧、动漫等）')
    drive_type = db.Column(db.String(50), nullable=False, comment='网盘类型（如百度云、阿里云、腾讯云等）')
    link = db.Column(db.Text, comment='网盘分享链接')
    is_expired = db.Column(db.Integer, nullable=False, default=1, comment='是否失效（0：有效，1：失效）')
    view_count = db.Column(db.Integer, nullable=False, default=0, comment='浏览次数')
    share_count = db.Column(db.Integer, nullable=False, default=0, comment='分享次数')
    hot = db.Column(db.Integer, nullable=False, default=0, comment='热度')
    size = db.Column(db.String(50), comment='文件大小')
    tmdb_id = db.Column(db.Integer, comment='影视资源信息ID')
    last_share_time = db.Column(db.DateTime, comment='上次分享时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='记录创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='记录修改时间')

    __table_args__ = (
        db.UniqueConstraint('drama_name', 'drive_type', name='uk_drama_drive'),
    )

    def to_dict(self):
        '''转换为字典'''
        return {
            'id': self.id,
            'drama_name': self.drama_name,
            'alias': self.alias,
            'category1': self.category1,
            'category2': self.category2,
            'drive_type': self.drive_type,
            'link': self.link,
            'is_expired': self.is_expired,
            'view_count': self.view_count,
            'share_count': self.share_count,
            'hot': self.hot,
            'size': self.size,
            'tmdb_id': self.tmdb_id,
            'last_share_time': self.last_share_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_share_time else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }
