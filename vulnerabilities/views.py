#
# Copyright (c) nexB Inc. and others. All rights reserved.
# VulnerableCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/vulnerablecode for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#

from django.db.models import Count
from django.db.models import Q
from django.http.response import HttpResponseNotAllowed
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from packageurl import PackageURL

from vulnerabilities import models
from vulnerabilities.forms import PackageForm
from vulnerabilities.forms import VulnerabilityForm

PAGE_SIZE = 50


class PackageSearchView(ListView):
    model = models.Package
    template_name = "packages.html"
    ordering = ["type", "namespace", "name", "version"]
    paginate_by = PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_query = self.request.GET
        context["package_form"] = PackageForm(request_query)
        context["package_name"] = request_query.get("package_name")
        return context

    def get_queryset(self, query=None):
        """
        Return a Package queryset for the ``query``.
        Make a best effort approach to find matching packages either based
        on exact purl, partial purl or just name and namespace.
        """
        qs = self.model.objects

        query = query or self.request.GET.get("package_name") or ""
        query = query.strip()
        if not query:
            return qs.none()

        if not query.startswith("pkg:"):
            # treat this as a plain search
            qs = qs.filter(Q(name__icontains=query) | Q(namespace__icontains=query))
        else:
            # this looks like a purl: check if it quacks like a purl
            purl_type = namespace = name = version = qualifiers = subpath = None

            _, _scheme, remainder = query.partition("pkg:")
            remainder = remainder.strip()
            if not remainder:
                return qs.none()

            try:
                # First, treat the query as a syntactically-correct purl
                purl = PackageURL.from_string(query)
                purl_type, namespace, name, version, qualifiers, subpath = purl.to_dict().values()
            except ValueError:
                # Otherwise, attempt a more lenient parsing of a possibly partial purl
                if "/" in remainder:
                    purl_type, _scheme, ns_name = remainder.partition("/")
                    ns_name = ns_name.strip()
                    if ns_name:
                        if "/" in ns_name:
                            namespace, _, name = ns_name.partition("/")
                        else:
                            name = ns_name
                        name = name.strip()
                        if name:
                            if "@" in name:
                                name, _, version = name.partition("@")
                                version = version.strip()
                                name = name.strip()
                else:
                    purl_type = remainder

            if purl_type:
                qs = qs.filter(type__iexact=purl_type)
            if namespace:
                qs = qs.filter(namespace__iexact=namespace)
            if name:
                qs = qs.filter(name__iexact=name)
            if version:
                qs = qs.filter(version__iexact=version)
            if qualifiers:
                qs = qs.filter(qualifiers=qualifiers)
            if subpath:
                qs = qs.filter(subpath__iexact=subpath)

        return qs.annotate(
            vulnerability_count=Count(
                "vulnerabilities",
                filter=Q(packagerelatedvulnerability__fix=False),
            ),
            patched_vulnerability_count=Count(
                "vulnerabilities",
                filter=Q(packagerelatedvulnerability__fix=True),
            ),
        ).prefetch_related()


class VulnerabilitySearchView(ListView):
    model = models.Vulnerability
    template_name = "vulnerabilities.html"
    ordering = ["vulnerability_id"]
    paginate_by = PAGE_SIZE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_query = self.request.GET
        context["vulnerability_form"] = VulnerabilityForm(request_query)
        context["vulnerability_id"] = request_query.get("vulnerability_id")
        return context

    def get_queryset(self, query=None):
        query = query or self.request.GET.get("vulnerability_id") or ""
        qs = self.model.objects
        if not query:
            return qs.none()
        qs = (
            qs.filter(
                Q(vulnerability_id__icontains=query)
                | Q(aliases__alias__icontains=query)
                | Q(references__id__icontains=query)
                | Q(summary__icontains=query)
            )
            .order_by("vulnerability_id")
            .annotate(
                vulnerable_package_count=Count(
                    "packages", filter=Q(packagerelatedvulnerability__fix=False), distinct=True
                ),
                patched_package_count=Count(
                    "packages", filter=Q(packagerelatedvulnerability__fix=True), distinct=True
                ),
            )
            .prefetch_related()
        )
        return qs


class PackageDetails(DetailView):
    model = models.Package
    template_name = "package_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.object
        context["package"] = package
        context["impacted_vuln"] = package.vulnerable_to.order_by("vulnerability_id")
        context["resolved_vuln"] = package.resolved_to.order_by("vulnerability_id")
        context["package_form"] = PackageForm(self.request.GET)
        return context


class VulnerabilityDetails(DetailView):
    model = models.Vulnerability
    template_name = "vulnerability_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vulnerability"] = self.object
        context["vulnerability_form"] = VulnerabilityForm(self.request.GET)
        context["severities"] = list(self.object.severities)
        return context


class HomePage(View):
    template_name = "index.html"

    def get(self, request):
        request_query = request.GET
        context = {
            "vulnerability_form": VulnerabilityForm(request_query),
            "package_form": PackageForm(request_query),
        }
        return render(request=request, template_name=self.template_name, context=context)


def schema_view(request):
    if request.method != "GET":
        return HttpResponseNotAllowed()
    return render(request=request, template_name="api_doc.html")
