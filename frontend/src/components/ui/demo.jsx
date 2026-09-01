export default function SocialProofRating({ className = "" }) {
    return (
        <div className={`flex flex-col sm:flex-row items-center justify-center sm:divide-x divide-gray-200 gap-3 sm:gap-0 ${className}`}>
            <div className="flex -space-x-2.5 sm:-space-x-3 sm:pr-4">
                <img
                    src="https://images.unsplash.com/photo-1633332755192-727a05c4013d?q=80&w=200"
                    alt="user avatar"
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white object-cover hover:-translate-y-1 transition-transform duration-200 z-[1] shadow-sm"
                />
                <img
                    src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?q=80&w=200"
                    alt="user avatar"
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white object-cover hover:-translate-y-1 transition-transform duration-200 z-[2] shadow-sm"
                />
                <img
                    src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=200&h=200&auto=format&fit=crop"
                    alt="user avatar"
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white object-cover hover:-translate-y-1 transition-transform duration-200 z-[3] shadow-sm"
                />
                <img
                    src="https://randomuser.me/api/portraits/men/75.jpg"
                    alt="user avatar"
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white object-cover hover:-translate-y-1 transition-transform duration-200 z-[4] shadow-sm"
                />
            </div>
            <div className="sm:pl-4 text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start gap-1">
                    {[...Array(5)].map((_, i) => (
                        <svg
                            key={i}
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="#FACC15"
                            stroke="#FACC15"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="drop-shadow-xs"
                        >
                            <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/>
                        </svg>
                    ))}
                    <p className="text-gray-900 font-bold text-sm ml-1.5">5.0</p>
                </div>
                <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
                    Trusted by <span className="font-bold text-gray-900">100,000+</span> freelancers and clients
                </p>
            </div>
        </div>
    );
}
