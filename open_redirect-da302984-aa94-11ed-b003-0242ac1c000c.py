import os
import shutil
import uuid
from factotum import settings
from pathlib import Path, PurePath

from django.db import models
from .common_info import CommonInfo
from django.urls import reverse
from django.db.models.signals import pre_save
from django.dispatch import receiver
from model_utils import FieldTracker
from django.core.exceptions import ValidationError

from .group_type import GroupType
from .extracted_text import ExtractedText
from .extracted_cpcat import ExtractedCPCat
from .extracted_chemical import ExtractedChemical
from .extracted_functional_use import ExtractedFunctionalUse
from .extracted_list_presence import ExtractedListPresence

# could be used for dynamically creating filename on instantiation
# in the 'upload_to' param on th FileField
def update_filename(instance, filename):
    name_fill_space = instance.name.replace(' ', '_')
    # potential space errors in name
    name = '{0}/{0}_{1}'.format(name_fill_space, filename)
    return name


def csv_upload_path(instance, filename):
    # potential space errors in name
    name = '{0}/{1}'.format(instance.fs_id, filename)
    return name

extract_models = {
    'CO': (ExtractedText, ExtractedChemical),
    'FU': (ExtractedText, ExtractedFunctionalUse),
    'CP': (ExtractedCPCat, ExtractedListPresence)
}



class DataGroup(CommonInfo):

    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    downloaded_by = models.ForeignKey('auth.User',
                                    on_delete=models.SET_DEFAULT, default = 1)
    downloaded_at = models.DateTimeField()
    download_script = models.ForeignKey('Script',
                                    on_delete=models.SET_NULL, default=None,
                                    null=True, blank=True)
    data_source = models.ForeignKey('DataSource', on_delete=models.CASCADE)
    fs_id = models.UUIDField(default=uuid.uuid4, editable=False)
    csv = models.FileField(upload_to=csv_upload_path, null=True)
    zip_file = models.CharField(max_length=100)
    group_type = models.ForeignKey(GroupType, on_delete=models.SET_DEFAULT,
                                            default=1, null=True, blank=True)
    url = models.CharField(max_length=150, blank=True)

    tracker = FieldTracker()

    @property
    def type(self):
        return str(self.group_type.code)

    @property
    def is_composition(self):
        return self.type == 'CO'

    @property
    def is_habits_and_practices(self):
        return self.type == 'HP'

    @property
    def is_functional_use(self):
        return self.type == 'FU'

    @property
    def is_chemical_presence(self):
        return self.type == 'CP'

    @property
    def is_hh(self):
        return self.type == 'HH'


    def get_extract_models(self):
        '''returns a tuple with parent/child extract models'''
        return extract_models.get(self.type)

    def save(self, *args, **kwargs):
        super(DataGroup, self).save(*args, **kwargs)

    def matched_docs(self):
        return self.datadocument_set.filter(matched=True).count()

    def all_matched(self):
        return all(self.datadocument_set.values_list('matched', flat=True))

    def all_extracted(self):
        return all(self.datadocument_set.values_list('extracted', flat=True))

    def registered_docs(self):
        return self.datadocument_set.count()

    def extracted_docs(self):
        return self.datadocument_set.filter(extracted=True).count()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('data_group_edit', kwargs={'pk': self.pk})

    def get_name_as_slug(self):
        return self.name.replace(' ', '_')

    def get_dg_folder(self):
        uuid_dir = f'{settings.MEDIA_ROOT}{str(self.fs_id)}'
        name_dir = f'{settings.MEDIA_ROOT}{self.get_name_as_slug()}'

        #this needs to handle missing csv files
        if bool(self.csv.name):
            # parse the media folder from the penultimate piece of csv file path
            p = PurePath(self.csv.path)
            csv_folder=p.parts[-2]
            csv_fullfolderpath   = f'{settings.MEDIA_ROOT}{csv_folder}'

        if os.path.isdir(uuid_dir):
            return uuid_dir # UUID-based folder
        elif bool(self.csv.name) and os.path.isdir(csv_fullfolderpath):
            return csv_fullfolderpath # csv path-based folder
        else:
            return 'no_folder_found'

    @property
    def dg_folder(self):
        '''This is a "falsy" property. If the folder cannot be found,
        dg.dg_folder evaluates to boolean False '''
        if self.get_dg_folder() != 'no_folder_found':
            return self.get_dg_folder()
        else:
            return False


    @property
    def csv_url(self):
        '''This is a "falsy" property. If the csv file cannot be found,
        dg.csv_url evaluates to boolean False '''
        try:
            self.csv.size
            csv_url = self.csv.url
        except ValueError:
            csv_url = False
        except:
            csv_url = False
        return csv_url


    @property
    def zip_url(self):
        '''This is a "falsy" property. If the zip file cannot be found,
        dg.zip_url evaluates to boolean False '''
        if self.get_zip_url()!='no_path_found':
            return(self.get_zip_url)
        else:
            return False
        

    def get_zip_url(self):
        # the path if the data group's folder was built from a UUID:
        uuid_path = f'{self.get_dg_folder()}/{str(self.fs_id)}.zip'
        # path if the data group's folder was built from old name-based method
        zip_file_path = f'{self.get_dg_folder()}/{self.get_name_as_slug()}.zip'
        if os.path.isfile(uuid_path):   # it is a newly-added data group
            zip_url = uuid_path
        elif os.path.isfile(zip_file_path): # it is a pre-UUID data group
            zip_url = zip_file_path
        else:
            zip_url = 'no_path_found'
        return zip_url


    def get_extracted_template_fieldnames(self):
        extract_fields = ['data_document_id','data_document_filename',
                            'prod_name', 'doc_date','rev_num', 'raw_category',
                            'raw_cas', 'raw_chem_name', 'report_funcuse']
        if self.type == 'FU':
            return extract_fields
        if self.type == 'CO':
            return extract_fields + ['raw_min_comp','raw_max_comp', 'unit_type',
                                        'ingredient_rank', 'raw_central_comp']
        if self.type == 'CP':
            for name in ['prod_name','rev_num','report_funcuse']:
                extract_fields.remove(name)
            return extract_fields + ['cat_code','description_cpcat',
                                    'cpcat_code','cpcat_sourcetype']

    def get_clean_comp_data_fieldnames(self):
        return ['id','lower_wf_analysis','central_wf_analysis', 'upper_wf_analysis']

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if self.tracker.has_changed('group_type_id') and self.extracted_docs():
            msg = "The Group Type may not be changed once extracted documents have been associated with the group."
            raise ValidationError({'group_type': msg})


@receiver(models.signals.post_delete, sender=DataGroup)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes datagroup directory from filesystem
    when datagroup instance is deleted.
    """
    dg_folder = instance.get_dg_folder()
    if os.path.isdir(dg_folder):
        #print('deleting folder %s for data group %s'%(dg_folder, instance.pk))
        shutil.rmtree(dg_folder)
