import re
from xml.dom.minidom import parseString

from django.db import models


def prettify_xml(xml_str):
    xml_str = re.sub(r'\s*\n\s*', '', xml_str)
    ugly = parseString(xml_str).toprettyxml(indent='    ')
    regex = re.compile(r'>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
    return regex.sub('>\g<1></', ugly)


class OrderTransaction(models.Model):
    
    # Note we don't use a foreign key as the order hasn't been created
    # by the time the transaction takes place
    order_number = models.CharField(max_length=128, db_index=True)
    
    # The 'method' of the transaction - one of 'auth', 'pre', 'cancel', ...
    method = models.CharField(max_length=12)
    amount = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    merchant_reference = models.CharField(max_length=128, blank=True, null=True)
    
    # Response fields
    datacash_reference = models.CharField(max_length=128, blank=True, null=True)
    auth_code = models.CharField(max_length=128, blank=True, null=True)
    status = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    
    # Store full XML for debugging purposes
    request_xml = models.TextField()
    response_xml = models.TextField()
    
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)
    
    def save(self, *args, **kwargs):
        # Ensure sensitive data isn't saved
        if not self.pk:
            cc_regex = re.compile(r'\d{12}')
            self.request_xml = cc_regex.sub('XXXXXXXXXXXX', self.request_xml)
            ccv_regex = re.compile(r'<cv2>\d+</cv2>')
            self.request_xml = ccv_regex.sub('<cv2>XXX</cv2>', self.request_xml)
            pw_regex = re.compile(r'<password>.*</password>')
            self.request_xml = pw_regex.sub('<password>XXX</password>', self.request_xml)
        super(OrderTransaction, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s txn for order %s - ref: %s, status: %s' % (
            self.method.upper(),
            self.order_number,
            self.datacash_reference,
            self.status)

    @property
    def pretty_request_xml(self):
        return prettify_xml(self.request_xml)

    @property
    def pretty_response_xml(self):
        return prettify_xml(self.response_xml)

