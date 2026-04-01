from app.services.signals.domain_signal import DomainAgeSignal
from app.services.signals.ssl_signal import SSLSignal
from app.services.signals.policy_pages_signal import PolicyPagesSignal
from app.services.signals.redflags_signal import RedFlagsSignal
from app.services.signals.github_signal import GitHubSignal
from app.services.signals.linkedin_signal import LinkedInSignal
from app.services.signals.claims_signal import ClaimsSignal
from app.core.scoring_config import scoring_settings

async def run_all_signals(company, context):
    extractors = [
        DomainAgeSignal(),
        SSLSignal(),
        PolicyPagesSignal(),
        RedFlagsSignal(),
        GitHubSignal(),
        LinkedInSignal(),
        ClaimsSignal(),
    ]

    # override dynamique via env/.env
    dynamic_weights = {
        "domain_age": scoring_settings.weight_domain_age,
        "ssl_certificate": scoring_settings.weight_ssl_certificate,
        "policy_pages_presence": scoring_settings.weight_policy_pages_presence,
        "red_flags": scoring_settings.weight_red_flags,
        "github_public_footprint": scoring_settings.weight_github_public_footprint,
        "linkedin_public_footprint": scoring_settings.weight_linkedin_public_footprint,
        "product_claims_quality": scoring_settings.weight_product_claims_quality,
    }

    results = []
    for ex in extractors:
        r = await ex.extract(company, context)
        r["weight"] = float(dynamic_weights.get(ex.key, ex.weight))
        results.append(r)
    return results