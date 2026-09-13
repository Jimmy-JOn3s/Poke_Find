export type CardLanguage = 'th' | 'en' | 'ja';
export type CardCondition = 'M' | 'NM' | 'LP' | 'MP' | 'HP';
export type UserRole = 'personal' | 'business';
export type ListingStatus = 'draft' | 'active' | 'reserved' | 'sold' | 'hidden' | 'completed';
export type AppLang = 'th' | 'en';
export type Currency = 'THB' | 'USD';
export type CardRarity = 'common' | 'uncommon' | 'rare' | 'ultra' | 'secret';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: UserRole;
  verified: boolean;
  verifiedType?: 'id' | 'passport';
  rating: number;
  reviewCount: number;
  totalSold: number;
  joinedDate: string;
  location: string;
  bio: string;
  preferredLanguage?: AppLang;
  preferredCurrency?: Currency;
}

export interface Listing {
  id: string;
  sellerId: string;
  sellerName: string;
  sellerAvatar: string;
  sellerRole: UserRole;
  sellerVerified: boolean;
  sellerRating: number;
  productName: string;
  set: string;
  setCode: string;
  cardNumber: string;
  condition: CardCondition;
  language: CardLanguage;
  rarity: CardRarity;
  listedPrice: number;
  currency?: Currency;
  finalPrice?: number;
  transactionDate?: string;
  quantity: number;
  soldQuantity?: number;
  status: ListingStatus;
  gradientFrom: string;
  gradientTo: string;
  typeIcon: string;
  createdAt: string;
  views: number;
  likes: number;
  description?: string;
  photo?: string;
  isSaved?: boolean;
}

export interface Message {
  id: string;
  senderId: string;
  senderName: string;
  text: string;
  timestamp: string;
  type: 'message' | 'offer' | 'offer_accepted' | 'offer_rejected' | 'system' | 'completed';
  offerAmount?: number;
}

export interface ChatThread {
  id: string;
  listingId: string;
  listingName: string;
  gradientFrom: string;
  gradientTo: string;
  buyerId: string;
  buyerName: string;
  buyerAvatar: string;
  sellerId: string;
  sellerName: string;
  sellerAvatar: string;
  messages: Message[];
  negotiatedPrice?: number;
  status: 'active' | 'completed' | 'rejected';
  lastMessage: string;
  lastMessageTime: string;
  unread: number;
  listedPrice: number;
}

export interface Review {
  id: string;
  reviewerId: string;
  reviewerName: string;
  reviewerAvatar: string;
  reviewerRole: UserRole;
  rating: number;
  comment: string;
  date: string;
}

export type Page = 'discover' | 'chat' | 'auth' | 'listing' | 'settings' | 'profile' | 'analytics';
