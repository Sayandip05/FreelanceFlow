from .services import (
    search_projects,
    search_freelancers,
    reindex_all,
)
from .services_saved import (
    save_search,
    get_saved_searches,
    delete_saved_search,
)
from .services_autocomplete import (
    record_search_term,
    get_autocomplete_suggestions,
)
from .services_history import (
    log_search,
    get_search_history,
    get_popular_searches,
)
