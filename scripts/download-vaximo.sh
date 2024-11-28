#!/bin/bash

# Array com todas as URLs
URLS=(
    "https://themes.hibootstrap.com/brito/"
    "https://themes.hibootstrap.com/brito/home-two/"
    "https://themes.hibootstrap.com/brito/home-three/"
    "https://themes.hibootstrap.com/brito/it-support/"
    "https://themes.hibootstrap.com/brito/co-managed-it/"
    "https://themes.hibootstrap.com/brito/cloud-services/"
    "https://themes.hibootstrap.com/brito/microsoft-azure/"
    "https://themes.hibootstrap.com/brito/voip-telecom/"
    "https://themes.hibootstrap.com/brito/onsite-office-moves/"
    "https://themes.hibootstrap.com/brito/endpoint-protection/"
    "https://themes.hibootstrap.com/brito/network-protection/"
    "https://themes.hibootstrap.com/brito/awarness-training/"
    "https://themes.hibootstrap.com/brito/backup-business-continuity/"
    "https://themes.hibootstrap.com/brito/soc-siem/"
    "https://themes.hibootstrap.com/brito/framework-certifications/"
    "https://themes.hibootstrap.com/brito/compliance-information-governance/"
    "https://themes.hibootstrap.com/brito/blog/"
    "https://themes.hibootstrap.com/brito/the-revolution-in-remote-work-how-managed-it-services-facilitate-a-flexible-work-environment/"
    "https://themes.hibootstrap.com/brito/about-us/"
    "https://themes.hibootstrap.com/brito/why-choose-us/"
    "https://themes.hibootstrap.com/brito/leadership-team/"
    "https://themes.hibootstrap.com/brito/team-post/jane-ronan/"
    "https://themes.hibootstrap.com/brito/career/"
    "https://themes.hibootstrap.com/brito/career-post/content-filtering/"
    "https://themes.hibootstrap.com/brito/pricing-plan/"
    "https://themes.hibootstrap.com/brito/contact-us/"
    "https://themes.hibootstrap.com/brito/faqs/"
    "https://themes.hibootstrap.com/brito/terms-conditions/"
    "https://themes.hibootstrap.com/brito/privacy-policy/"
    "https://themes.hibootstrap.com/brito/architecture-design/"
    "https://themes.hibootstrap.com/brito/automotive/"
    "https://themes.hibootstrap.com/brito/biotechnology/"
    "https://themes.hibootstrap.com/brito/construction/"
    "https://themes.hibootstrap.com/brito/finance-insurance/"
    "https://themes.hibootstrap.com/brito/healthcare/"
    "https://themes.hibootstrap.com/brito/law-offices-law-firms/"
    "https://themes.hibootstrap.com/brito/logistics-distribution/"
    "https://themes.hibootstrap.com/brito/manufacturing/"
    "https://themes.hibootstrap.com/brito/non-profit/"
    "https://themes.hibootstrap.com/brito/retail/"
    "https://themes.hibootstrap.com/brito/shop/"
    "https://themes.hibootstrap.com/brito/product/magazine-book/"
    "https://themes.hibootstrap.com/brito/cart/"
    "https://themes.hibootstrap.com/brito/checkout/"
    "https://themes.hibootstrap.com/brito/my-account/"
    "https://themes.hibootstrap.com/brito/contact-us/"
    "https://themes.hibootstrap.com/brito/contact"
)

# Comando wget base
wget \
  --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --span-hosts \
  --domains=themes.envytheme.com,cdn.envytheme.com,fonts.googleapis.com,fonts.gstatic.com \
  --reject-regex "logout|signout|cart|checkout|wp-admin" \
  --no-parent \
  --wait=1 \
  --random-wait \
  --recursive \
  --level=inf \
  --restrict-file-names=windows \
  --content-disposition \
  "${URLS[@]}"