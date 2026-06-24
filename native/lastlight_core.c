#include <stddef.h>
#include <string.h>

int lastlight_count_matches(
    const char **query_tokens,
    size_t query_count,
    const char **document_tokens,
    size_t document_count
) {
    int matches = 0;
    for (size_t i = 0; i < query_count; i++) {
        for (size_t j = 0; j < document_count; j++) {
            if (strcmp(query_tokens[i], document_tokens[j]) == 0) {
                matches++;
                break;
            }
        }
    }
    return matches;
}

