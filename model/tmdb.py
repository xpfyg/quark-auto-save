# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from db import db


class Tmdb(db.Model):
    '''
    TMDB剧集信息表（含年份）
    '''
    __tablename__ = 'tmdb'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    tmdb_code = db.Column(db.String(255), nullable=False, comment='tmdb的剧编号')
    title = db.Column(db.String(255), nullable=False, comment='剧的名称')
    year_released = db.Column(db.Integer, comment='上映/发行年份（如2023）')
    category = db.Column(db.String(100), comment='分类（如剧情、喜剧、科幻等）')
    description = db.Column(db.Text, comment='剧情描述')
    poster_url = db.Column(db.String(500), comment='海报图片链接')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='记录创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='记录更新时间')

    __table_args__ = (
        db.UniqueConstraint('title', 'year_released', name='uk_title_year'),
    )

    def to_dict(self):
        '''转换为字典'''
        return {
            'id': self.id,
            'tmdb_code': self.tmdb_code,
            'title': self.title,
            'year_released': self.year_released,
            'category': self.category,
            'description': self.description,
            'poster_url': self.poster_url,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }
