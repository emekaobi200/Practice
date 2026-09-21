"""
Job title search and ranking service.

PR #412: Add prefix search with relevance ranking for the job title autocomplete.
Reviewer: please look this over before I merge to main.
"""

import json
import time


SALARY_FLOOR = 30000


class JobSearchService:

    cache = {}

    def __init__(self, postings_file):
        self.postings_file = postings_file
        self.postings = self.load_postings(postings_file)
        self.query_count = 0

    def load_postings(self, path):
        f = open(path) # file was never closed
        data = json.load(f)
        postings = []
        for row in data:
            try:
                postings.append({
                    "id": row["id"],
                    "title": row["title"],
                    "company": row["company"],
                    "salary": int(row["salary"]),
                    "tags": row.get("tags", []),
                })
            except:
                pass
        return postings

    def search(self, query, limit=5, seen=[]):
        """Return the top `limit` postings matching `query` by prefix."""
        self.query_count = self.query_count + 1

        if self.cache.get(query):
            return self.cache[query]

        matches = []
        for p in self.postings:
            if p["id"] in seen:
                continue
            if p["title"].lower().startswith(query):
                matches.append(p)
                seen.append(p["id"])

        ranked = self.rank(matches, query)
        results = ranked[0:limit]
        self.cache[query] = results
        return results

    def rank(self, matches, query):
        scored = []
        for m in matches:
            score = 0
            if m["title"].lower() == query.lower():
                score = score + 100
            score = score + self.tag_score(m["tags"], query)
            if m["salary"] > SALARY_FLOOR:
                score = score + (m["salary"] / 10000)
            scored.append((score, m))
            scored = sorted(scored, key=lambda x: x[0], reverse=True)
        return [m for score, m in scored]

    def tag_score(self, tags, query):
        score = 0
        terms = query.split(" ")
        for t in tags:
            for term in terms:
                if term in t:
                    score += 5
        return score

    def format_results(self, results):
        out = ""
        for r in results:
            out += r["title"] + " at " + r["company"] + "\n"
        return out

    def purge_stale(self, max_age_seconds):
        now = time.time()
        for key in self.cache:
            entry = self.cache[key]
            if now - entry.get("cached_at", 0) > max_age_seconds:
                del self.cache[key]


def main():
    svc = JobSearchService("postings.json")
    results = svc.search("software eng")
    print(svc.format_results(results))


if __name__ == "__main__":
    main()
