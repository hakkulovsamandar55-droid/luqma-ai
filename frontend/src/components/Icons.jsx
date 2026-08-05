/** Inline SVG ikonkalar — tashqi kutubxonasiz, currentColor bilan bo'yaladi. */

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

function Svg({ size = 24, children, ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...rest}>
      {children}
    </svg>
  )
}

export const HomeIcon = (p) => (
  <Svg {...p}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5.5 9.5V20a1 1 0 0 0 1 1H10v-6h4v6h3.5a1 1 0 0 0 1-1V9.5" />
  </Svg>
)

export const GearIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.2" />
    <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 9 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 9a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z" />
  </Svg>
)

export const PlusIcon = (p) => (
  <Svg strokeWidth={2.4} {...p}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
)

export const CameraIcon = (p) => (
  <Svg {...p}>
    <path d="M4 8h3l1.6-2.4A1 1 0 0 1 9.4 5h5.2a1 1 0 0 1 .8.6L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" />
    <circle cx="12" cy="13.5" r="3.4" />
  </Svg>
)

export const GalleryIcon = (p) => (
  <Svg {...p}>
    <rect x="3" y="4" width="18" height="16" rx="2.5" />
    <circle cx="8.5" cy="9.5" r="1.6" />
    <path d="m3.5 17 4.6-4.6a1.6 1.6 0 0 1 2.3 0l3.4 3.4m0 0 1.9-1.9a1.6 1.6 0 0 1 2.3 0l2.5 2.5" />
  </Svg>
)

export const PencilIcon = (p) => (
  <Svg {...p}>
    <path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z" />
    <path d="m14.5 5.5 4 4" />
  </Svg>
)

export const ChevronRight = (p) => (
  <Svg strokeWidth={2} {...p}>
    <path d="m9 5 7 7-7 7" />
  </Svg>
)

export const CloseIcon = (p) => (
  <Svg strokeWidth={2.2} {...p}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Svg>
)

export const TrashIcon = (p) => (
  <Svg {...p}>
    <path d="M4 7h16M9.5 7V5.5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V7" />
    <path d="M6.5 7 7.4 19a1 1 0 0 0 1 .9h7.2a1 1 0 0 0 1-.9L17.5 7" />
    <path d="M10.5 11v5M13.5 11v5" />
  </Svg>
)

/* Oqsil — gantel (sport bilan assotsiatsiya, kichik o'lchamda ham o'qiladi) */
export const ProteinIcon = (p) => (
  <Svg {...p}>
    <path d="M3.5 10v4M6.8 8v8M17.2 8v8M20.5 10v4" />
    <path d="M6.8 12h10.4" />
  </Svg>
)

export const CarbsIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3c1.6 2.4 1.6 4.8 0 7.2-1.6 2.4-1.6 4.8 0 7.2" />
    <path d="M7 8c1.2 1.8 1.2 3.6 0 5.4M17 8c-1.2 1.8-1.2 3.6 0 5.4" />
    <path d="M5 20h14" />
  </Svg>
)

export const FatIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3.5c3.2 3.6 5 6.4 5 9a5 5 0 0 1-10 0c0-2.6 1.8-5.4 5-9Z" />
  </Svg>
)

export const FireIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3c.6 2.6-.6 4-2 5.4C8.3 10 7 11.6 7 14a5 5 0 0 0 10 0c0-1.8-.7-3-1.7-4.2-.5 1-1.3 1.5-2 1.6.8-2.4.3-5.4-1.3-8.4Z" />
  </Svg>
)

/* Suv — stakan (yog' ikonkasi bilan chalkashmasligi uchun tomchi emas) */
export const WaterIcon = (p) => (
  <Svg {...p}>
    <path d="M6.2 4h11.6l-1.3 15.6a1.6 1.6 0 0 1-1.6 1.4H9.1a1.6 1.6 0 0 1-1.6-1.4L6.2 4Z" />
    <path d="M7.1 11.5h9.8" />
  </Svg>
)

export const ScaleIcon = (p) => (
  <Svg {...p}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="3" />
    <path d="M8.5 10.5 12 8l3.5 2.5" />
    <path d="M12 8v3.5" />
  </Svg>
)

export const UserIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="8.5" r="3.6" />
    <path d="M4.8 20a7.2 7.2 0 0 1 14.4 0" />
  </Svg>
)

/* Yosh — kalendar */
export const CalendarIcon = (p) => (
  <Svg {...p}>
    <rect x="3.5" y="5" width="17" height="15.5" rx="2.8" />
    <path d="M8 3v4M16 3v4M3.5 10h17" />
  </Svg>
)

/* Jins — ikki kishi (neytral belgi) */
export const GenderIcon = (p) => (
  <Svg {...p}>
    <circle cx="9" cy="8.4" r="3.3" />
    <path d="M3.2 19.4a5.8 5.8 0 0 1 11.6 0" />
    <path d="M16.2 5.6a3.3 3.3 0 0 1 0 5.6" />
    <path d="M17.6 13.2a5.8 5.8 0 0 1 3.2 5.2" />
  </Svg>
)

export const PhoneIcon = (p) => (
  <Svg {...p}>
    <path d="M6.5 3.5h3l1.4 3.5-2 1.4a11 11 0 0 0 5.2 5.2l1.4-2 3.5 1.4v3a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 4.5 5.7a2 2 0 0 1 2-2.2Z" />
  </Svg>
)

export const RulerIcon = (p) => (
  <Svg {...p}>
    <rect x="2.5" y="8" width="19" height="8" rx="2" />
    <path d="M7 8v3M11 8v4M15 8v3M19 8v4" />
  </Svg>
)

export const TargetIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="4.5" />
    <circle cx="12" cy="12" r="1" fill="currentColor" />
  </Svg>
)

export const ActivityIcon = (p) => (
  <Svg {...p}>
    <path d="M3 12h4l2.5-6 4 13 2.5-7H21" />
  </Svg>
)

export const ChartIcon = (p) => (
  <Svg {...p}>
    <path d="M4 20V4" />
    <path d="M4 20h16" />
    <path d="M8 16v-4M12.5 16V8M17 16v-6" />
  </Svg>
)

export const StarIcon = (p) => (
  <Svg {...p}>
    <path d="m12 4 2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.5-4.8 2.5.9-5.4L4.2 9.7l5.4-.8L12 4Z" />
  </Svg>
)

export const SupportIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .9-1 1.6v.3" />
    <path d="M12 16.8h.01" />
  </Svg>
)

export const SparkIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3.5 13.4 8l4.5 1.4-4.5 1.4L12 15.3l-1.4-4.5L6.1 9.4 10.6 8 12 3.5Z" />
    <path d="M18.5 15.5 19.2 17.4l1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7.7-1.9Z" />
  </Svg>
)

export const ArrowDownIcon = (p) => (
  <Svg strokeWidth={2} {...p}>
    <path d="M12 4v14" />
    <path d="m6.5 12.5 5.5 5.5 5.5-5.5" />
  </Svg>
)

export const CheckIcon = (p) => (
  <Svg strokeWidth={2.4} {...p}>
    <path d="m5 12.5 4.5 4.5L19 7" />
  </Svg>
)

/* Ovqat — bug' chiqayotgan kosa (TargetIcon bilan chalkashmaydi) */
export const PlateIcon = (p) => (
  <Svg {...p}>
    <path d="M3.2 11h17.6a8.8 8.8 0 0 1-17.6 0Z" />
    <path d="M8.8 7.6c0-1 1-1.5 1-2.6M12 7.2c0-1.1 1-1.6 1-2.7M15.2 7.6c0-1 1-1.5 1-2.6" />
  </Svg>
)
