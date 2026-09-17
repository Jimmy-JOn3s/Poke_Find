import type { AppLang } from './types';

const th = {
  // Navigation
  discover: 'ค้นหา', chat: 'แชท', profile: 'โปรไฟล์', settings: 'ตั้งค่า', signIn: 'เข้าสู่ระบบ',

  // Discover
  discoverTitle: 'ค้นพบการ์ด', searchPlaceholder: 'ค้นหาการ์ด Pokémon...', filter: 'กรอง', sort: 'เรียง',
  allConditions: 'ทุกสภาพ', allLanguages: 'ทุกภาษา', allSets: 'ทุกเซต', newListing: 'ลงขายใหม่',
  sortNewest: 'ใหม่สุด', sortPopular: 'ยอดนิยม', sortPriceLow: '฿ ต่ำ→สูง', sortPriceHigh: '฿ สูง→ต่ำ',
  noResults: 'ไม่พบการ์ดที่ค้นหา', noResultsSub: 'ลองค้นหาด้วยคำอื่น',

  // Listing fields
  condition: 'สภาพการ์ด', language: 'ภาษาการ์ด', set: 'เซต', cardNumber: 'เลขการ์ด',
  listedPrice: 'ราคาตั้ง', finalPrice: 'ราคาสุดท้าย', quantity: 'จำนวน', sellerType: 'ประเภทผู้ขาย',
  createListing: 'ลงขาย', editListing: 'แก้ไขรายการ', deleteListing: 'ลบรายการ',
  contactSeller: 'ติดต่อผู้ขาย', makeOffer: 'เสนอราคา', buyNow: 'ซื้อเลย',  

  // Conditions
  M: 'มินต์', NM: 'เกือบมินต์', LP: 'เล่นเบา', MP: 'เล่นปานกลาง', HP: 'เล่นหนัก',

  // Card languages
  th: 'ไทย', en: 'อังกฤษ', ja: 'ญี่ปุ่น',

  // Auth
  welcomeBack: 'ยินดีต้อนรับ', createAccount: 'สมัครสมาชิก',
  email: 'อีเมล', password: 'รหัสผ่าน', fullName: 'ชื่อ-นามสกุล',
  continueWithGoogle: 'เข้าสู่ระบบด้วย Google', magicLink: 'ส่งลิงก์เข้าสู่ระบบ',
  personalAccount: 'บัญชีส่วนตัว', businessAccount: 'บัญชีธุรกิจ',
  personalDesc: 'สำหรับผู้ซื้อขายทั่วไป', businessDesc: 'สำหรับร้านค้าและผู้ขายรายใหญ่',
  verification: 'ยืนยันตัวตน', uploadId: 'อัปโหลดบัตรประชาชน / พาสปอร์ต',
  verificationDesc: 'เพื่อความปลอดภัย กรุณายืนยันตัวตนก่อนเริ่มขาย',
  idCard: 'บัตรประชาชน', passport: 'พาสปอร์ต', pending: 'รอการตรวจสอบ',
  pendingDesc: 'เราจะตรวจสอบเอกสารของคุณภายใน 24 ชั่วโมง คุณจะได้รับอีเมลแจ้งผล',
  or: 'หรือ',
  linkSent: 'ส่งลิงก์แล้ว',
  linkSentTo: 'ส่งลิงก์ไปที่',
  secureNote: 'ข้อมูลของคุณถูกเข้ารหัสและปลอดภัย ใช้เพื่อยืนยันตัวตนเท่านั้น',
  uploadFront: 'อัปโหลดด้านหน้า', uploadBack: 'อัปโหลดด้านหลัง',
  uploaded: 'อัปโหลดแล้ว',
  skipForNow: 'ข้ามสำหรับตอนนี้', completeVerification: 'ยืนยันตัวตน',
  startUsing: 'เริ่มใช้งาน',

  // Chat
  chatTitle: 'ข้อความ', noChats: 'ยังไม่มีการสนทนา', typeMessage: 'พิมพ์ข้อความ...',
  sendOffer: 'ส่งข้อเสนอ', offerPrice: 'ราคาที่เสนอ (฿)', accept: 'ยอมรับ', reject: 'ปฏิเสธ',
  markCompleted: 'บันทึกการซื้อขาย', transactionComplete: 'การซื้อขายเสร็จสิ้น',
  offerSent: 'ส่งข้อเสนอราคา', offerAccepted: 'ยอมรับข้อเสนอแล้ว', offerRejected: 'ปฏิเสธข้อเสนอ',
  enterOffer: 'ใส่ราคาที่ต้องการเสนอ', finalTransactionPrice: 'ราคาที่ตกลง',
  selling: 'ขาย', buying: 'ซื้อ', txSuccess: 'สำเร็จ',
  completedMsg: 'บันทึกการซื้อขายแล้ว',

  // Profile
  totalSold: 'ยอดขาย', rating: 'คะแนน', reviews: 'รีวิว', activeListings: 'รายการ',
  verified: 'ยืนยันแล้ว', notVerified: 'ยังไม่ยืนยัน', businessBadge: 'BIZ',
  joinedOn: 'สมาชิกตั้งแต่',   noReviews: 'ยังไม่มีรีวิว', noListings: 'ยังไม่มีรายการ',
  verifyToSell: 'ยืนยันตัวตนเพื่อขายได้',
  leaveReview: 'เขียนรีวิว', reviewPromptTitle: 'การซื้อขายสำเร็จ!',
  reviewPromptBody: 'ช่วยให้คะแนนและรีวิวเพื่อสร้างความน่าเชื่อถือให้ชุมชน',
  reviewFor: 'รีวิว', reviewComment: 'ความคิดเห็น (ไม่บังคับ)',
  reviewPlaceholder: 'เล่าประสบการณ์การซื้อขายของคุณ...',
  reviewSubmitted: 'ส่งรีวิวแล้ว ขอบคุณ!', reviewLater: 'ไว้ทีหลัง',
  reviewBanner: 'ทิ้งรีวิวให้', yourRating: 'คะแนนของคุณ',

  // Settings
  settingsTitle: 'ตั้งค่า', notifications: 'การแจ้งเตือน', pushNotifications: 'การแจ้งเตือนแบบพุช',
  pushNotifSub: 'แจ้งเตือนการซื้อขายและข้อความ',
  emailNotifications: 'การแจ้งเตือนทางอีเมล', emailNotifSub: 'รับอีเมลสรุปรายสัปดาห์',
  chatNotifications: 'แจ้งเตือนแชทใหม่', chatNotifSub: 'เมื่อมีข้อความหรือข้อเสนอ',
  priceAlerts: 'แจ้งเตือนราคา', priceAlertsSub: 'เมื่อการ์ดที่บันทึกไว้ลดราคา',
  appLanguage: 'ภาษาแอป', appearance: 'รูปลักษณ์', lightMode: 'สว่าง', darkMode: 'มืด', systemTheme: 'ระบบ',
  signOut: 'ออกจากระบบ',
  account: 'บัญชีของฉัน', security: 'ความปลอดภัย', help: 'ช่วยเหลือ',
  privacy: 'นโยบายความเป็นส่วนตัว', terms: 'ข้อกำหนดการใช้งาน', version: 'เวอร์ชัน',

  // Analytics
  analyticsTitle: 'วิเคราะห์ธุรกิจ', revenue: 'รายได้รวม', transactions: 'ธุรกรรม',
  avgRating: 'คะแนนเฉลี่ย', topCards: 'การ์ดขายดี', recentSales: 'การขายล่าสุด',
  lastSixMonths: '6 เดือนล่าสุด', perMonth: 'ครั้ง/เดือน', avgTx: 'เฉลี่ย',
  txCount: 'จำนวนธุรกรรม',

  // General
  baht: '฿', save: 'บันทึก', cancel: 'ยกเลิก', confirm: 'ยืนยัน', back: 'กลับ', next: 'ถัดไป',
  submit: 'ส่ง', loading: 'กำลังโหลด...', sold: 'ขายแล้ว', available: 'มีสินค้า',
  completed: 'เสร็จสิ้น', personal: 'ส่วนตัว', business: 'ธุรกิจ',
  views: 'ยอดดู', likes: 'ถูกใจ', postedOn: 'ลงเมื่อ', cardDetails: 'รายละเอียดการ์ด',
  sellerInfo: 'ข้อมูลผู้ขาย', description: 'รายละเอียด', productName: 'ชื่อการ์ด',
  step: 'ขั้นตอน', of: '/', chooseRole: 'เลือกประเภทบัญชี', verifyIdentity: 'ยืนยันตัวตน',
  soldQuantity: 'จำนวนที่ขายแล้ว', transactionDate: 'วันที่ทำรายการ',
  analytics: 'วิเคราะห์', businessOnly: 'สำหรับบัญชีธุรกิจเท่านั้น',
  viewAllListings: 'ดูรายการทั้งหมด', deleteConfirm: 'คุณแน่ใจหรือว่าต้องการลบรายการนี้?',
  deleteWarning: 'การดำเนินการนี้ไม่สามารถย้อนกลับได้',
  raritySecret: '✦ Secret Rare', rarityUltra: '◆ Ultra Rare', rarityRare: '◇ Rare',
  selectSet: '-- เลือกเซต --', typeIconLabel: 'ไอคอนประเภท',
  previewLabel: 'ตรวจสอบรายการ', negotiationNote: 'ราคาสุดท้ายสามารถต่อรองได้ผ่านฟีเจอร์แชท',
  businessFeatures: 'ฟีเจอร์ธุรกิจ',
  displayCurrency: 'สกุลเงินที่แสดง', thaiBaht: 'บาทไทย', usDollar: 'ดอลลาร์สหรัฐ',
  tryAgain: 'ลองอีกครั้ง', networkError: 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้',
};

const en: typeof th = {
  discover: 'Discover', chat: 'Chat', profile: 'Profile', settings: 'Settings', signIn: 'Sign In',

  discoverTitle: 'Discover Cards', searchPlaceholder: 'Search Pokémon cards...', filter: 'Filter', sort: 'Sort',
  allConditions: 'All Conditions', allLanguages: 'All Languages', allSets: 'All Sets', newListing: 'New Listing',
  sortNewest: 'Newest', sortPopular: 'Popular', sortPriceLow: '฿ Low→High', sortPriceHigh: '฿ High→Low',
  noResults: 'No cards found', noResultsSub: 'Try a different search term',

  condition: 'Condition', language: 'Card Language', set: 'Set', cardNumber: 'Card No.',
  listedPrice: 'Listed Price', finalPrice: 'Final Price', quantity: 'Quantity', sellerType: 'Seller Type',
  createListing: 'List a Card', editListing: 'Edit Listing', deleteListing: 'Delete Listing',
  contactSeller: 'Contact Seller', makeOffer: 'Make Offer', buyNow: 'Buy Now',

  M: 'Mint', NM: 'Near Mint', LP: 'Lightly Played', MP: 'Moderately Played', HP: 'Heavily Played',

  th: 'Thai', en: 'English', ja: 'Japanese',

  welcomeBack: 'Welcome Back', createAccount: 'Create Account',
  email: 'Email', password: 'Password', fullName: 'Full Name',
  continueWithGoogle: 'Continue with Google', magicLink: 'Send Magic Link',
  personalAccount: 'Personal Account', businessAccount: 'Business Account',
  personalDesc: 'For casual buyers and sellers', businessDesc: 'For shops and high-volume sellers',
  verification: 'Identity Verification', uploadId: 'Upload ID / Passport',
  verificationDesc: 'For security, verify your identity before selling',
  idCard: 'National ID', passport: 'Passport', pending: 'Pending Review',
  pendingDesc: 'We\'ll review your document within 24 hours. You\'ll receive an email with the result.',
  or: 'or',
  linkSent: 'Link sent',
  linkSentTo: 'Link sent to',
  secureNote: 'Your data is encrypted and secure. Used for identity verification only.',
  uploadFront: 'Upload Front', uploadBack: 'Upload Back',
  uploaded: 'Uploaded',
  skipForNow: 'Skip for Now', completeVerification: 'Complete Verification',
  startUsing: 'Get Started',

  chatTitle: 'Messages', noChats: 'No conversations yet', typeMessage: 'Type a message...',
  sendOffer: 'Send Offer', offerPrice: 'Offer Price (฿)', accept: 'Accept', reject: 'Reject',
  markCompleted: 'Mark as Completed', transactionComplete: 'Transaction Complete',
  offerSent: 'Offer Sent', offerAccepted: 'Offer Accepted', offerRejected: 'Offer Rejected',
  enterOffer: 'Enter your offer amount', finalTransactionPrice: 'Agreed Price',
  selling: 'Selling', buying: 'Buying', txSuccess: 'Complete',
  completedMsg: 'Transaction recorded',

  totalSold: 'Sold', rating: 'Rating', reviews: 'Reviews', activeListings: 'Listings',
  verified: 'Verified', notVerified: 'Not Verified', businessBadge: 'BIZ',
  joinedOn: 'Member since',   noReviews: 'No reviews yet', noListings: 'No listings yet',
  verifyToSell: 'Verify to start selling',
  leaveReview: 'Leave a Review', reviewPromptTitle: 'Transaction Complete!',
  reviewPromptBody: 'Rate your trading partner to help build trust in the community.',
  reviewFor: 'Review', reviewComment: 'Comment (optional)',
  reviewPlaceholder: 'Share your trading experience...',
  reviewSubmitted: 'Review submitted. Thank you!', reviewLater: 'Maybe later',
  reviewBanner: 'Leave a review for', yourRating: 'Your rating',

  settingsTitle: 'Settings', notifications: 'Notifications', pushNotifications: 'Push Notifications',
  pushNotifSub: 'Trade activity and messages',
  emailNotifications: 'Email Notifications', emailNotifSub: 'Weekly summary emails',
  chatNotifications: 'Chat Notifications', chatNotifSub: 'New messages and offers',
  priceAlerts: 'Price Alerts', priceAlertsSub: 'When saved cards drop in price',
  appLanguage: 'App Language', appearance: 'Appearance', lightMode: 'Light', darkMode: 'Dark', systemTheme: 'System',
  signOut: 'Sign Out',
  account: 'My Account', security: 'Security', help: 'Help & Support',
  privacy: 'Privacy Policy', terms: 'Terms of Service', version: 'Version',

  analyticsTitle: 'Business Analytics', revenue: 'Total Revenue', transactions: 'Transactions',
  avgRating: 'Avg Rating', topCards: 'Top Selling Cards', recentSales: 'Recent Sales',
  lastSixMonths: 'Last 6 months', perMonth: '/month', avgTx: 'avg',
  txCount: 'Transaction Count',

  baht: '฿', save: 'Save', cancel: 'Cancel', confirm: 'Confirm', back: 'Back', next: 'Next',
  submit: 'Submit', loading: 'Loading...', sold: 'Sold', available: 'Available',
  completed: 'Completed', personal: 'Personal', business: 'Business',
  views: 'Views', likes: 'Likes', postedOn: 'Posted', cardDetails: 'Card Details',
  sellerInfo: 'Seller Info', description: 'Description', productName: 'Card Name',
  step: 'Step', of: 'of', chooseRole: 'Choose Account Type', verifyIdentity: 'Verify Identity',
  soldQuantity: 'Qty Sold', transactionDate: 'Transaction Date',
  analytics: 'Analytics', businessOnly: 'Business accounts only',
  viewAllListings: 'View All Listings', deleteConfirm: 'Delete this listing?',
  deleteWarning: 'This action cannot be undone.',
  raritySecret: '✦ Secret Rare', rarityUltra: '◆ Ultra Rare', rarityRare: '◇ Rare',
  selectSet: '-- Select Set --', typeIconLabel: 'Type Icon',
  previewLabel: 'Review Listing', negotiationNote: 'Final price can be negotiated through chat',
  businessFeatures: 'Business Features',
  displayCurrency: 'Display Currency', thaiBaht: 'Thai baht', usDollar: 'US dollar',
  tryAgain: 'Try again', networkError: 'Could not reach the server',
};

export const i18n: Record<AppLang, typeof th> = { th, en };
export type T = typeof th;
