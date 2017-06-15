#! /usr/bin/env python
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it to the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


class Model(CRUDMixin, db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True


class Burndown(Model):
    id = db.Column(db.Integer, primary_key=True)
    total_jobs = db.Column(db.Numeric, nullable=False, default=0)
    finished_jobs = db.Column(db.Numeric, nullable=False, default=0)
    captured_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, total_jobs, finished_jobs, captured_date, **kwargs):
        db.Model.__init__(self, total_jobs=total_jobs, finished_jobs=finished_jobs,
                          captured_date=captured_date,
                          **kwargs)

    def __repr__(self):
        return "<Burndown, Total: {} , Done: {}, Time created: {}".format(
                self.total_jobs, self.finished_jobs, str(self.captured_date))

    def to_json(self):
        dict_representation = {}
        dict_representation["total_jobs"] = str(self.total_jobs)
        dict_representation["finished_jobs"] = str(self.finished_jobs)
        dict_representation["captured_date"] = datetime.strftime(self.captured_date, format="%a %b %d %H:%M:%S %Z %Y")
        return dict_representation

