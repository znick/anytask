# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Year'
        db.create_table('years_year', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start_year', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
        ))
        db.send_create_signal('years', ['Year'])


    def backwards(self, orm):
        
        # Deleting model 'Year'
        db.delete_table('years_year')


    models = {
        'years.year': {
            'Meta': {'object_name': 'Year'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_year': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['years']
