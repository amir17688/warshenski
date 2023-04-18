from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView, DetailView
from .forms import SearchForm
from lib.geoip import GeoIP
from lib.vt import VT
from lib.threatminer import ThreatMiner
import socket
from django.db.models import Q
from apps.threat.models import Event, Attribute
from apps.reputation.models import blacklist
from apps.twitter.models import tweet
from apps.exploit.models import Exploit

class IndexView(TemplateView):
    template_name = 'ip/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        return context

    def get(self, request, **kwargs):
        if request.GET.get('keyword'):
            ip = request.GET.get('keyword')
            return HttpResponseRedirect(ip)
        context = self.get_context_data()
        return self.render_to_response(context)

class DetailView(TemplateView):
    template_name = 'ip/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        ip = self.kwargs['pk']
        context['geoip'] = GeoIP().lookup(ip)
        try:
            context['domain'] = socket.gethostbyaddr(ip)[0]
        except Exception as e:
            pass

        vt = VT()
        context['vt_ip'] = vt.getIPReport(ip)

        tm = ThreatMiner()
        context['tm_url'] = tm.getURIFromIP(ip)
        context['tm_sample'] = tm.getSamplesFromIP(ip)
        context['tm_report'] = tm.getReportFromIP(ip)

        context['bls'] = blacklist.objects.filter(Q(ip=ip)|Q(url__contains=ip))
        count = context['bls'].count()
        if count > 0:
            context['bls_count'] = count
        context['events'] = Event.objects.filter(Q(info__icontains=ip)).order_by('-publish_timestamp')
        count = context['events'].count()
        if count > 0:
            context['events_count'] = count
        context['attributes'] = Attribute.objects.filter(Q(value__icontains=ip)).order_by('-timestamp')
        count = context['attributes'].count()
        if count > 0:
            context['attributes_count'] = count
        context['tws'] = tweet.objects.filter(Q(text__icontains=ip)).order_by('-datetime')
        count = context['tws'].count()
        if count > 0:
            context['tws_count'] = count
        context['exs'] = Exploit.objects.filter(Q(text__icontains=ip)).order_by('-datetime')
        count = context['exs'].count()
        if count > 0:
            context['exs_count'] = count

        return context

