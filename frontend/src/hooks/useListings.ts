import { useCallback, useEffect, useState } from "react";
import type { Listing } from "../types";
import { api, mapListing, type ListingFilters } from "../lib/api";


export function useListings(filters: ListingFilters = {}) {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const filterKey = JSON.stringify(filters);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setListings(await api.listListings(filters));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [filterKey]);

  useEffect(() => { void reload(); }, [reload]);

  const create = async (payload: Record<string, unknown>) => {
    const item = mapListing(await api.createListing(payload));
    setListings(current => [item, ...current]);
    return item;
  };

  const remove = async (id: string) => {
    await api.deleteListing(id);
    setListings(current => current.filter(item => item.id !== id));
  };

  return { listings, loading, error, reload, create, remove, setListings };
}

