'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import {
  MagnifyingGlassIcon,
  FireIcon,
  SparklesIcon,
  TrophyIcon,
  HeartIcon,
  StarIcon,
  ChevronDownIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon, StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import Image from 'next/image';
import Link from 'next/link';

// Types
interface Product {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  creator_name: string;
  creator_avatar?: string;
  category_name: string;
  category_slug: string;
  product_type: string;
  price: number;
  sale_price?: number;
  currency: string;
  featured_image?: string;
  is_featured: boolean;
  is_marketplace_promoted: boolean;
  is_trending: boolean;
  is_new: boolean;
  average_rating?: number;
  review_count: number;
  view_count: number;
  trending_score: number;
  sales_count_24h: number;
  revenue_24h: number;
  tags: Array<{
    id: string;
    name: string;
    color: string;
  }>;
  published_at: string;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  product_count: number;
  trending_count: number;
}

interface MarketplaceStats {
  total_products: number;
  active_creators: number;
  today_sales: number;
  trending_count: number;
}

// API functions
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = {
  async getMarketplaceData(params: {
    page?: number;
    category?: string;
    search?: string;
    sort_by?: string;
    filter?: string;
  }) {
    const query = new URLSearchParams({
      page: params.page?.toString() || '1',
      page_size: '20',
      ...(params.category && { category: params.category }),
      ...(params.search && { search: params.search }),
      ...(params.sort_by && { sort_by: params.sort_by }),
      ...(params.filter && { filter: params.filter }),
    });

    const response = await fetch(`${API_BASE}/marketplace/api/marketplace/?${query}`);
    if (!response.ok) throw new Error('Failed to fetch products');
    return response.json();
  },

  async getTrendingProducts() {
    const response = await fetch(`${API_BASE}/marketplace/api/trending/`);
    if (!response.ok) throw new Error('Failed to fetch trending products');
    return response.json();
  },

  async getSearchSuggestions(query: string) {
    const response = await fetch(`${API_BASE}/marketplace/api/search-suggestions/?q=${encodeURIComponent(query)}`);
    if (!response.ok) return { suggestions: { products: [], categories: [], tags: [] } };
    return response.json();
  },

  async getMarketplaceStats() {
    const response = await fetch(`${API_BASE}/marketplace/api/stats/`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },

  async trackInteraction(productId: string, type: string, duration?: number) {
    try {
      await fetch(`${API_BASE}/marketplace/api/track-interaction/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: productId,
          type,
          duration,
        }),
      });
    } catch (error) {
      console.error('Failed to track interaction:', error);
    }
  },
};

// Components
const SearchBar: React.FC<{
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
}> = ({ value, onChange, onSearch }) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const getSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const data = await api.getSearchSuggestions(query);
      const allSuggestions = [
        ...data.suggestions.products,
        ...data.suggestions.categories,
        ...data.suggestions.tags,
      ].slice(0, 5);
      setSuggestions(allSuggestions);
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    }
  }, []);

  useEffect(() => {
    const debounce = setTimeout(() => getSuggestions(value), 300);
    return () => clearTimeout(debounce);
  }, [value, getSuggestions]);

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="relative">
        <input
          type="text"
          placeholder="Search products, creators, categories..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          className="w-full px-6 py-4 text-lg rounded-full border-0 shadow-lg text-gray-800 focus:ring-4 focus:ring-blue-300 focus:outline-none"
        />
        <button
          onClick={onSearch}
          className="absolute right-2 top-2 bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 transition"
        >
          <MagnifyingGlassIcon className="w-6 h-6" />
        </button>
      </div>

      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 bg-white rounded-lg shadow-xl mt-2 py-2 z-50"
          >
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  onChange(suggestion);
                  setShowSuggestions(false);
                  onSearch();
                }}
              >
                {suggestion}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const ProductCard: React.FC<{
  product: Product;
  size?: 'small' | 'medium' | 'large';
}> = ({ product, size = 'medium' }) => {
  const [isLiked, setIsLiked] = useState(false);
  const [imageError, setImageError] = useState(false);

  const cardSizes = {
    small: 'h-32',
    medium: 'h-48',
    large: 'h-64',
  };

  const handleProductClick = () => {
    api.trackInteraction(product.id, 'view');
  };

  const handleLikeClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsLiked(!isLiked);
    api.trackInteraction(product.id, 'like');
  };

  const badges = [];
  if (product.is_marketplace_promoted) badges.push({ text: 'Featured', color: 'bg-yellow-100 text-yellow-800' });
  if (product.is_trending) badges.push({ text: '🔥 Trending', color: 'bg-red-100 text-red-800' });
  if (product.is_new) badges.push({ text: 'New', color: 'bg-green-100 text-green-800' });

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer"
      onClick={handleProductClick}
    >
      <div className="relative">
        <div className={`relative ${cardSizes[size]} bg-gray-200`}>
          {!imageError && product.featured_image ? (
            <Image
              src={product.featured_image}
              alt={product.title}
              fill
              className="object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
              <SparklesIcon className="w-12 h-12 text-gray-400" />
            </div>
          )}
        </div>

        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {badges.map((badge, index) => (
            <span
              key={index}
              className={`px-2 py-1 rounded-full text-xs font-semibold ${badge.color}`}
            >
              {badge.text}
            </span>
          ))}
        </div>

        {/* Like Button */}
        <button
          onClick={handleLikeClick}
          className="absolute top-2 right-2 p-2 bg-white rounded-full shadow-md hover:bg-gray-100 transition"
        >
          {isLiked ? (
            <HeartSolidIcon className="w-5 h-5 text-red-500" />
          ) : (
            <HeartIcon className="w-5 h-5 text-gray-600" />
          )}
        </button>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-lg mb-2 line-clamp-2">{product.title}</h3>
        {size !== 'small' && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">{product.short_description}</p>
        )}

        <div className="flex items-center mb-3">
          <div className="w-6 h-6 rounded-full bg-gray-300 mr-2 overflow-hidden">
            {product.creator_avatar ? (
              <Image
                src={product.creator_avatar}
                alt={product.creator_name}
                width={24}
                height={24}
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-blue-500 flex items-center justify-center text-white text-xs">
                {product.creator_name.charAt(0)}
              </div>
            )}
          </div>
          <span className="text-sm text-gray-700">{product.creator_name}</span>
        </div>

        <div className="flex items-center justify-between mb-4">
          {product.average_rating && (
            <div className="flex items-center">
              <div className="flex items-center text-yellow-400 mr-2">
                {[...Array(5)].map((_, i) => (
                  <StarSolidIcon
                    key={i}
                    className={`w-4 h-4 ${
                      i < Math.floor(product.average_rating!) ? 'text-yellow-400' : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-600">({product.review_count})</span>
            </div>
          )}

          <div className="text-right">
            {product.sale_price && product.sale_price < product.price ? (
              <div className="flex flex-col">
                <span className="text-lg font-bold text-green-600">
                  R{product.sale_price.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500 line-through">
                  R{product.price.toFixed(2)}
                </span>
              </div>
            ) : (
              <span className="text-lg font-bold text-gray-900">
                R{product.price.toFixed(2)}
              </span>
            )}
          </div>
        </div>

        <Link href={`/products/${product.slug}`}>
          <button className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition font-medium">
            View Product
          </button>
        </Link>
      </div>
    </motion.div>
  );
};

const CategoryFilter: React.FC<{
  categories: Category[];
  selected: string;
  onChange: (category: string) => void;
}> = ({ categories, selected, onChange }) => {
  return (
    <div className="flex flex-wrap gap-2 justify-center py-4">
      <button
        onClick={() => onChange('all')}
        className={`px-4 py-2 rounded-full font-medium transition ${
          selected === 'all'
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-100'
        }`}
      >
        All Products
      </button>
      {categories.map((category) => (
        <button
          key={category.id}
          onClick={() => onChange(category.slug)}
          className={`px-4 py-2 rounded-full font-medium transition ${
            selected === category.slug
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          {category.name} ({category.product_count})
        </button>
      ))}
    </div>
  );
};

// Main Marketplace Component
const MarketplaceDiscovery: React.FC<{
  initialData?: {
    featuredProducts: Product[];
    trendingProducts: Product[];
    newArrivals: Product[];
    categories: Category[];
    stats: MarketplaceStats;
  };
}> = ({ initialData }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>(initialData?.featuredProducts || []);
  const [trendingProducts, setTrendingProducts] = useState<Product[]>(initialData?.trendingProducts || []);
  const [newArrivals, setNewArrivals] = useState<Product[]>(initialData?.newArrivals || []);
  const [categories, setCategories] = useState<Category[]>(initialData?.categories || []);
  const [stats, setStats] = useState<MarketplaceStats>(initialData?.stats || {
    total_products: 0,
    active_creators: 0,
    today_sales: 0,
    trending_count: 0,
  });

  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('trending');
  const [filterType, setFilterType] = useState('all');

  const { ref: loadMoreRef, inView } = useInView({
    threshold: 0,
  });

  const loadProducts = useCallback(async (reset = false) => {
    if (loading || (!hasMore && !reset)) return;

    setLoading(true);
    try {
      const currentPage = reset ? 1 : page;
      const data = await api.getMarketplaceData({
        page: currentPage,
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        search: searchQuery || undefined,
        sort_by: sortBy,
        filter: filterType,
      });

      if (reset) {
        setProducts(data.results);
        setPage(2);
      } else {
        setProducts(prev => [...prev, ...data.results]);
        setPage(prev => prev + 1);
      }

      setHasMore(data.has_next);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, page, selectedCategory, searchQuery, sortBy, filterType]);

  // Load initial products
  useEffect(() => {
    loadProducts(true);
  }, [selectedCategory, sortBy, filterType]);

  // Infinite scroll
  useEffect(() => {
    if (inView && hasMore && !loading) {
      loadProducts();
    }
  }, [inView, hasMore, loading, loadProducts]);

  // Search handling
  const handleSearch = () => {
    loadProducts(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-6xl font-bold font-heading mb-4">
              Discover Digital Products
            </h1>
            <p className="text-xl md:text-2xl mb-8 opacity-90">
              From South African creators, for the world
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              onSearch={handleSearch}
            />
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 text-center"
          >
            <div>
              <div className="text-2xl font-bold">{stats.total_products.toLocaleString()}</div>
              <div className="text-sm opacity-75">Products</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.active_creators.toLocaleString()}</div>
              <div className="text-sm opacity-75">Creators</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.today_sales.toLocaleString()}</div>
              <div className="text-sm opacity-75">Sales Today</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.trending_count.toLocaleString()}</div>
              <div className="text-sm opacity-75">Trending</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Category Navigation */}
      <section className="bg-gray-100 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <CategoryFilter
            categories={categories}
            selected={selectedCategory}
            onChange={setSelectedCategory}
          />
        </div>
      </section>

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section className="py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 font-heading flex items-center">
                <TrophyIcon className="w-8 h-8 text-yellow-500 mr-2" />
                Featured Products
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts.slice(0, 8).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Trending Products */}
      {trendingProducts.length > 0 && (
        <section className="py-12 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 font-heading flex items-center">
                <FireIcon className="w-8 h-8 text-red-500 mr-2" />
                Trending Now
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {trendingProducts.slice(0, 8).map((product) => (
                <ProductCard key={product.id} product={product} size="medium" />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* New Arrivals */}
      {newArrivals.length > 0 && (
        <section className="py-12 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 font-heading flex items-center">
                <SparklesIcon className="w-8 h-8 text-green-500 mr-2" />
                New Arrivals
              </h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {newArrivals.slice(0, 12).map((product) => (
                <ProductCard key={product.id} product={product} size="small" />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* All Products */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 font-heading">All Products</h2>

            {/* Controls */}
            <div className="flex gap-4">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                <option value="trending">Trending</option>
                <option value="newest">Newest</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="rating">Top Rated</option>
                <option value="sales">Best Selling</option>
              </select>

              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                <option value="all">All Products</option>
                <option value="featured">Featured</option>
                <option value="new">New Arrivals</option>
                <option value="trending">Trending</option>
              </select>
            </div>
          </div>

          {/* Products Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {/* Loading */}
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading products...</p>
            </div>
          )}

          {/* Load More Trigger */}
          <div ref={loadMoreRef} className="h-10" />

          {/* No More Products */}
          {!loading && !hasMore && products.length > 0 && (
            <div className="text-center py-8">
              <p className="text-gray-600">You've seen all products!</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default MarketplaceDiscovery;
