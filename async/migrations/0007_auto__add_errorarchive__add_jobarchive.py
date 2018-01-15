# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ErrorArchive'
        db.create_table('async_errorarchive', (
            ('error_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='errors', to=orm['async.JobArchive'])),
            ('executed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('exception', self.gf('django.db.models.fields.TextField')()),
            ('traceback', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('async', ['ErrorArchive'])

        # Adding model 'JobArchive'
        db.create_table('async_jobarchive', (
            ('job_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('args', self.gf('django.db.models.fields.TextField')()),
            ('kwargs', self.gf('django.db.models.fields.TextField')()),
            ('meta', self.gf('django.db.models.fields.TextField')()),
            ('result', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
            ('identity', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('scheduled', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('executed', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('cancelled', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('fairness', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('async', ['JobArchive'])


    def backwards(self, orm):
        # Deleting model 'ErrorArchive'
        db.delete_table('async_errorarchive')

        # Deleting model 'JobArchive'
        db.delete_table('async_jobarchive')


    models = {
        'async.error': {
            'Meta': {'object_name': 'Error'},
            'exception': ('django.db.models.fields.TextField', [], {}),
            'executed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'errors'", 'to': "orm['async.Job']"}),
            'traceback': ('django.db.models.fields.TextField', [], {})
        },
        'async.errorarchive': {
            'Meta': {'object_name': 'ErrorArchive'},
            'error_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'exception': ('django.db.models.fields.TextField', [], {}),
            'executed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'errors'", 'to': "orm['async.JobArchive']"}),
            'traceback': ('django.db.models.fields.TextField', [], {})
        },
        'async.group': {
            'Meta': {'object_name': 'Group'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'final': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ends'", 'null': 'True', 'to': "orm['async.Job']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'async.job': {
            'Meta': {'object_name': 'Job'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'args': ('django.db.models.fields.TextField', [], {}),
            'cancelled': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'executed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fairness': ('django.db.models.fields.IntegerField', [], {'default': '-1', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'jobs'", 'null': 'True', 'to': "orm['async.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {}),
            'meta': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'scheduled': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'async.jobarchive': {
            'Meta': {'object_name': 'JobArchive'},
            'added': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'args': ('django.db.models.fields.TextField', [], {}),
            'cancelled': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'executed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fairness': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'job_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {}),
            'meta': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'scheduled': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['async']