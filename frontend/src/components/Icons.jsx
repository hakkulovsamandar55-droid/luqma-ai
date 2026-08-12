/**
 * Inline SVG ikonkalar — tashqi kutubxonasiz, currentColor bilan bo'yaladi.
 *
 * DIZAYN QOIDALARI (o'zgartirganda buzmang):
 * - 24x24 to'r, chetdan 2px bo'sh joy (optik markaz).
 * - Chiziq qalinligi 1.7 — nozik, lekin kichik o'lchamda ham ko'rinadi.
 * - Barcha uch va burilishlar dumaloq (round cap/join) — o'tkir burchak yo'q.
 * - Burchak radiusi hech qachon 2px dan kichik emas; to'rtburchaklarda rx >= 3.
 * - "Uchli" shakllar (yulduz, olov, tomchi) egri chiziq bilan yumshatilgan.
 */

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  vectorEffect: 'non-scaling-stroke',
}

function Svg({ size = 24, children, ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} {...rest}>
      {children}
    </svg>
  )
}

/* ---------- Navigatsiya ---------- */

export const HomeIcon = (p) => (
  <Svg {...p}>
    <path d="M4 10.6a2 2 0 0 1 .74-1.55l6-4.8a2 2 0 0 1 2.52 0l6 4.8A2 2 0 0 1 20 10.6v7.9a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 18.5Z" />
    <path d="M9.75 21v-4.75a2.25 2.25 0 0 1 4.5 0V21" />
  </Svg>
)

export const GearIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.1" />
    <path d="M10.3 3.9a1.9 1.9 0 0 1 3.4 0l.4.8a1.9 1.9 0 0 0 2.1 1l.9-.2a1.9 1.9 0 0 1 1.9 2.9l-.5.8a1.9 1.9 0 0 0 0 2.1l.5.8a1.9 1.9 0 0 1-1.9 2.9l-.9-.2a1.9 1.9 0 0 0-2.1 1l-.4.8a1.9 1.9 0 0 1-3.4 0l-.4-.8a1.9 1.9 0 0 0-2.1-1l-.9.2a1.9 1.9 0 0 1-1.9-2.9l.5-.8a1.9 1.9 0 0 0 0-2.1l-.5-.8a1.9 1.9 0 0 1 1.9-2.9l.9.2a1.9 1.9 0 0 0 2.1-1Z" />
  </Svg>
)

export const PlusIcon = (p) => (
  <Svg strokeWidth={2.1} {...p}>
    <path d="M12 5.75v12.5M5.75 12h12.5" />
  </Svg>
)

export const ChevronRight = (p) => (
  <Svg strokeWidth={1.9} {...p}>
    <path d="m9.75 5.75 5.6 5.6a.92.92 0 0 1 0 1.3l-5.6 5.6" />
  </Svg>
)

export const CloseIcon = (p) => (
  <Svg strokeWidth={1.9} {...p}>
    <path d="M6.75 6.75 17.25 17.25M17.25 6.75 6.75 17.25" />
  </Svg>
)

export const CheckIcon = (p) => (
  <Svg strokeWidth={2.1} {...p}>
    <path d="m5.75 12.5 3.9 3.9a.6.6 0 0 0 .9 0L18.25 8.5" />
  </Svg>
)

export const ArrowDownIcon = (p) => (
  <Svg strokeWidth={1.9} {...p}>
    <path d="M12 4.75v13.5" />
    <path d="m6.9 13.4 4.45 4.45a.92.92 0 0 0 1.3 0l4.45-4.45" />
  </Svg>
)

export const SearchIcon = (p) => (
  <Svg {...p}>
    <circle cx="10.9" cy="10.9" r="6.15" />
    <path d="m15.6 15.6 3.65 3.65" />
  </Svg>
)

/* ---------- Kiritish ---------- */

export const CameraIcon = (p) => (
  <Svg {...p}>
    <path d="M4.5 8.25h2.4a1.6 1.6 0 0 0 1.36-.76l.86-1.4a1.6 1.6 0 0 1 1.36-.76h3.04a1.6 1.6 0 0 1 1.36.76l.86 1.4a1.6 1.6 0 0 0 1.36.76h2.4a2.5 2.5 0 0 1 2.5 2.5v6.5a2.5 2.5 0 0 1-2.5 2.5h-15a2.5 2.5 0 0 1-2.5-2.5v-6.5a2.5 2.5 0 0 1 2.5-2.5Z" />
    <circle cx="12" cy="13.9" r="3.1" />
  </Svg>
)

export const GalleryIcon = (p) => (
  <Svg {...p}>
    <rect x="3.75" y="4.75" width="16.5" height="14.5" rx="3.4" />
    <circle cx="8.9" cy="9.6" r="1.5" />
    <path d="M4.1 16.6l3.5-3.5a1.9 1.9 0 0 1 2.7 0l2.9 2.9m0 0 1.6-1.6a1.9 1.9 0 0 1 2.7 0l2.4 2.4" />
  </Svg>
)

export const PencilIcon = (p) => (
  <Svg {...p}>
    <path d="M4.75 19.25h3.1a1 1 0 0 0 .71-.29l9.3-9.3a2.35 2.35 0 0 0-3.32-3.32l-9.3 9.3a1 1 0 0 0-.29.71Z" />
    <path d="m13.9 6.9 3.2 3.2" />
  </Svg>
)

export const TrashIcon = (p) => (
  <Svg {...p}>
    <path d="M4.75 7.25h14.5" />
    <path d="M9.75 7.25V6.1a1.35 1.35 0 0 1 1.35-1.35h1.8A1.35 1.35 0 0 1 14.25 6.1v1.15" />
    <path d="M6.6 7.25 7.4 18.4a2 2 0 0 0 2 1.85h5.2a2 2 0 0 0 2-1.85l.8-11.15" />
    <path d="M10.6 11.1v5M13.4 11.1v5" />
  </Svg>
)

export const DownloadIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3.75v10" />
    <path d="m8.2 10.2 3.15 3.15a.92.92 0 0 0 1.3 0l3.15-3.15" />
    <path d="M4.5 17v1.75a2.5 2.5 0 0 0 2.5 2.5h10a2.5 2.5 0 0 0 2.5-2.5V17" />
  </Svg>
)

export const PlayIcon = (p) => (
  <Svg {...p}>
    <path d="M9 6.6a1 1 0 0 1 1.52-.85l7.4 4.55a1.4 1.4 0 0 1 0 2.4l-7.4 4.55A1 1 0 0 1 9 16.4Z" />
  </Svg>
)

/* ---------- Makro va oziqlanish ---------- */

/* Oqsil — gantel */
export const ProteinIcon = (p) => (
  <Svg {...p}>
    <path d="M3.6 10.4v3.2M20.4 10.4v3.2" />
    <rect x="6.1" y="7.8" width="2.9" height="8.4" rx="1.45" />
    <rect x="15" y="7.8" width="2.9" height="8.4" rx="1.45" />
    <path d="M9 12h6" />
  </Svg>
)

/* Uglevod — boshoq */
export const CarbsIcon = (p) => (
  <Svg {...p}>
    <path d="M12 20.25V9.5" />
    <path d="M12 9.5c0-2.2 1.2-4.1 3-5 .5 2.3-.4 4.4-3 5Z" />
    <path d="M12 9.5c0-2.2-1.2-4.1-3-5-.5 2.3.4 4.4 3 5Z" />
    <path d="M12 14.6c0-2.1 1.2-3.7 3-4.5.5 2.2-.4 4-3 4.5Z" />
    <path d="M12 14.6c0-2.1-1.2-3.7-3-4.5-.5 2.2.4 4 3 4.5Z" />
  </Svg>
)

/* Yog' — tomchi (uchi yumshoq egri) */
export const FatIcon = (p) => (
  <Svg {...p}>
    <path d="M12 4.4c.55.9 1.3 1.95 2.25 3.15A18.6 18.6 0 0 1 16.9 11a5.15 5.15 0 0 1-4.9 7.6 5.15 5.15 0 0 1-4.9-7.6 18.6 18.6 0 0 1 2.65-3.45C10.7 6.35 11.45 5.3 12 4.4Z" />
  </Svg>
)

/* Olov — tashqi til va ichki yadro.
   Ilgari kontur juda burilishli edi: 19px da tafsilotlar bir-biriga
   yopishib, tomchiga o'xshab qolardi. Endi ikkita sodda shakl. */
export const FireIcon = (p) => (
  <Svg {...p}>
    <path d="M12.4 3.05a.4.4 0 0 1 .66.3c.05 2.2 1.1 3.3 2.4 4.6 1.6 1.6 2.9 3.3 2.9 5.75a6.36 6.36 0 0 1-12.72 0c0-2.2 1-3.9 2.15-5.2a.4.4 0 0 1 .7.26c.02.95.3 1.7.8 2.25.6-3.35 2.05-5.85 3.11-7.96Z" />
    <path d="M12 14.15c1.05 1.15 1.7 2.05 1.7 3a2.35 2.35 0 0 1-4.7 0c0-.95.65-1.85 1.7-3 .25-.28.45-.53.65-.8.2.27.4.52.65.8Z" />
  </Svg>
)

/* Ovqat — bug' chiqayotgan kosa */
export const PlateIcon = (p) => (
  <Svg {...p}>
    <path d="M3.9 11.25h16.2a1 1 0 0 1 1 1.1 9.15 9.15 0 0 1-18.2 0 1 1 0 0 1 1-1.1Z" />
    <path d="M9.2 8.15c0-.9.85-1.35.85-2.35M12 7.75c0-1 .85-1.45.85-2.45M14.8 8.15c0-.9.85-1.35.85-2.35" />
  </Svg>
)

export const AppleIcon = (p) => (
  <Svg {...p}>
    <path d="M12 8.6a4.05 4.05 0 0 0-4.15-.3C6.4 9.15 5.75 11.2 6.3 13.3c.6 2.15 2.05 4.45 3.6 5.15.9.4 1.45.05 2.1.05s1.2.35 2.1-.05c1.55-.7 3-3 3.6-5.15.55-2.1-.1-4.15-1.55-5a4.05 4.05 0 0 0-4.15.3Z" />
    <path d="M12 8.6V7.2a2.45 2.45 0 0 1 2.45-2.45" />
  </Svg>
)

/* Suv — stakan */
export const WaterIcon = (p) => (
  <Svg {...p}>
    <path d="M6.6 4.75h10.8a.9.9 0 0 1 .9 1l-1.2 13.1a1.9 1.9 0 0 1-1.9 1.7H8.8a1.9 1.9 0 0 1-1.9-1.7L5.7 5.75a.9.9 0 0 1 .9-1Z" />
    <path d="M7.4 11.6h9.2" />
  </Svg>
)

/* ---------- Vaqt guruhlari ---------- */

export const SunriseIcon = (p) => (
  <Svg {...p}>
    <path d="M12 4.75v2.1M6.3 7.4l1.5 1.5M17.7 7.4l-1.5 1.5" />
    <path d="M7.85 14.9a4.15 4.15 0 0 1 8.3 0" />
    <path d="M4.25 18.4h15.5" />
  </Svg>
)

export const SunIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.9" />
    <path d="M12 3.75v1.6M12 18.65v1.6M5.15 5.15l1.15 1.15M17.7 17.7l1.15 1.15M3.75 12h1.6M18.65 12h1.6M5.15 18.85 6.3 17.7M17.7 6.3l1.15-1.15" />
  </Svg>
)

export const MoonIcon = (p) => (
  <Svg {...p}>
    <path d="M19.6 14.35A8.15 8.15 0 0 1 9.65 4.4a8.35 8.35 0 1 0 9.95 9.95Z" />
  </Svg>
)

/* ---------- Profil va o'lchov ---------- */

export const UserIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="8.6" r="3.5" />
    <path d="M5.25 19.75a6.75 6.75 0 0 1 13.5 0" />
  </Svg>
)

export const CalendarIcon = (p) => (
  <Svg {...p}>
    <rect x="3.75" y="5.25" width="16.5" height="15" rx="3.4" />
    <path d="M8.25 3.75v3M15.75 3.75v3M3.75 10h16.5" />
  </Svg>
)

/* Jins — Mars va Venera belgilari.
   Ilgari "ikki kishi" chizilgan edi, u esa "foydalanuvchilar" degan
   ma'noni beradi, jinsni emas. */
export const GenderIcon = (p) => (
  <Svg {...p}>
    <circle cx="9.4" cy="14.3" r="4.15" />
    <path d="M12.4 11.3 18.9 4.8" />
    <path d="M14.6 4.8h4.3v4.3" />
  </Svg>
)

export const PhoneIcon = (p) => (
  <Svg {...p}>
    <path d="M7 4.25h2.15a1 1 0 0 1 .94.65l1.1 2.85a1 1 0 0 1-.36 1.18l-1.35.95a10.4 10.4 0 0 0 4.6 4.6l.95-1.35a1 1 0 0 1 1.18-.36l2.85 1.1a1 1 0 0 1 .65.94V17a2.5 2.5 0 0 1-2.72 2.5A15.85 15.85 0 0 1 4.5 6.97 2.5 2.5 0 0 1 7 4.25Z" />
  </Svg>
)

/* Bo'y — vertikal o'lchov chizig'i.
   Ilgari yotiq "chizg'ich" edi: 19px da u batareyaga o'xshab qolar va
   bo'yni anglatmasdi. Endi ikki uchida strelka bor tik chiziq — bu
   universal "balandlik" belgisi. */
export const RulerIcon = (p) => (
  <Svg {...p}>
    {/* Yuqori va pastki chegara — o'lchov shu ikkisi orasida */}
    <path d="M5.4 4.6h13.2M5.4 19.4h13.2" />
    <path d="M12 7.2v9.6" />
    <path d="m9.7 9.5 2.3-2.3 2.3 2.3" />
    <path d="m9.7 14.5 2.3 2.3 2.3-2.3" />
  </Svg>
)

/* Vazn — tarozi: dumaloq shkala va strelka.
   Ilgari to'rtburchak ichida yuqoriga qaragan strelka bor edi — u
   "yuklash" (upload) belgisiga o'xshardi va vaznni bildirmasdi. */
export const ScaleIcon = (p) => (
  <Svg {...p}>
    {/* Strelkali shkala. Ilgari to'rtburchak ichiga kichik yoy chizilgan
        edi — 19px da u tafsilot emas, dog' bo'lib ko'rinardi. Endi yoy
        butun maydonni egallaydi. */}
    <path d="M4.4 17.9a8 8 0 1 1 15.2 0" />
    <path d="M4.4 17.9h15.2" />
    <path d="m12 17.9 4.3-5.1" />
  </Svg>
)

export const TargetIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.1" />
    <circle cx="12" cy="12" r="4.3" />
    <circle cx="12" cy="12" r="1.15" fill="currentColor" stroke="none" />
  </Svg>
)

/* Istalgan vazn — bayroq. Ilgari "Maqsad" bilan bir xil nishon ikonkasi
   turardi: ikki qatorda bir xil belgi ko'ringanda ro'yxat o'qilmaydi. */
export const FlagIcon = (p) => (
  <Svg {...p}>
    <path d="M6.25 20.25V4.6" />
    <path d="M6.25 5.4h9.9a.75.75 0 0 1 .58 1.22l-2.1 2.6a.75.75 0 0 0 0 .95l2.1 2.6a.75.75 0 0 1-.58 1.23h-9.9" />
  </Svg>
)

/* Premium — toj. Faqat obuna bo'limida ishlatiladi. */
export const CrownIcon = (p) => (
  <Svg {...p}>
    <path d="M4.4 8.1a1 1 0 0 1 1.62-.78l2.7 2.14a1 1 0 0 0 1.5-.3l1.9-3.55a1 1 0 0 1 1.76 0l1.9 3.55a1 1 0 0 0 1.5.3l2.7-2.14a1 1 0 0 1 1.61.78l-.9 7.3a2.2 2.2 0 0 1-2.18 1.93H7.49a2.2 2.2 0 0 1-2.19-1.94Z" />
    <path d="M8.6 20.4h6.8" />
  </Svg>
)

/* ---------- Statistika ---------- */

/* Faollik — puls chizig'i. Amplituda oshirildi: ilgari chiziq deyarli
   tekis edi va 19px da oddiy tire bo'lib ko'rinardi. */
export const ActivityIcon = (p) => (
  <Svg {...p}>
    <path d="M3.4 12.4h3a.9.9 0 0 0 .84-.58l1.85-4.9a.55.55 0 0 1 1.04.05l2.9 10.9a.55.55 0 0 0 1.06.01l1.72-5.85a.9.9 0 0 1 .86-.64h3.93" />
  </Svg>
)

export const ChartIcon = (p) => (
  <Svg {...p}>
    <path d="M4.25 3.75v14.6a1.9 1.9 0 0 0 1.9 1.9h13.6" />
    <path d="M8.6 16.3v-3.2M12.5 16.3V8.9M16.4 16.3v-5.3" />
  </Svg>
)

/* ---------- Holat va yordam ---------- */

export const StarIcon = (p) => (
  <Svg {...p}>
    <path d="M12 4.6a.55.55 0 0 1 .5.31l1.93 3.92a.55.55 0 0 0 .41.3l4.33.63a.55.55 0 0 1 .3.94l-3.13 3.05a.55.55 0 0 0-.16.49l.74 4.3a.55.55 0 0 1-.8.58l-3.87-2.04a.55.55 0 0 0-.51 0L7.87 19.1a.55.55 0 0 1-.8-.58l.74-4.3a.55.55 0 0 0-.16-.49l-3.13-3.05a.55.55 0 0 1 .3-.94l4.33-.63a.55.55 0 0 0 .41-.3L11.5 4.9a.55.55 0 0 1 .5-.31Z" />
  </Svg>
)

export const SupportIcon = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.1" />
    <path d="M9.75 9.7a2.35 2.35 0 1 1 3.2 2.2 1.7 1.7 0 0 0-1 1.55v.3" />
    <path d="M11.95 16.55h.1" strokeWidth={2.1} />
  </Svg>
)

export const BellIcon = (p) => (
  <Svg {...p}>
    <path d="M17.75 9.4a5.75 5.75 0 1 0-11.5 0c0 4.4-1.2 6-1.85 6.7a.7.7 0 0 0 .5 1.2h14.2a.7.7 0 0 0 .5-1.2c-.65-.7-1.85-2.3-1.85-6.7Z" />
    <path d="M13.75 19.6a2 2 0 0 1-3.5 0" />
  </Svg>
)

export const SparkIcon = (p) => (
  <Svg {...p}>
    <path d="M11.4 4.35a.62.62 0 0 1 1.2 0l.95 3.05a.62.62 0 0 0 .4.4l3.05.95a.62.62 0 0 1 0 1.2l-3.05.95a.62.62 0 0 0-.4.4l-.95 3.05a.62.62 0 0 1-1.2 0l-.95-3.05a.62.62 0 0 0-.4-.4L7 9.95a.62.62 0 0 1 0-1.2l3.05-.95a.62.62 0 0 0 .4-.4Z" />
    <path d="M18.1 15.9a.45.45 0 0 1 .85 0l.42 1.25a.45.45 0 0 0 .28.28l1.25.42a.45.45 0 0 1 0 .85l-1.25.42a.45.45 0 0 0-.28.28l-.42 1.25a.45.45 0 0 1-.85 0l-.42-1.25a.45.45 0 0 0-.28-.28l-1.25-.42a.45.45 0 0 1 0-.85l1.25-.42a.45.45 0 0 0 .28-.28Z" />
  </Svg>
)

/** AI / Murabbiy — suhbat pufakchasi ichida uchqun. */
export const AiIcon = (p) => (
  <Svg {...p}>
    <path d="M20.25 11.7a8.05 8.05 0 0 1-8.6 8.05 8.7 8.7 0 0 1-3.05-.6l-3.9 1.05a.7.7 0 0 1-.87-.87l1.05-3.9a8 8 0 0 1-.63-3.23 8.05 8.05 0 0 1 8.05-8.05 8.05 8.05 0 0 1 7.95 7.55Z" />
    <path d="M11.7 8.9a.5.5 0 0 1 .95 0l.5 1.45a.5.5 0 0 0 .3.3l1.45.5a.5.5 0 0 1 0 .95l-1.45.5a.5.5 0 0 0-.3.3l-.5 1.45a.5.5 0 0 1-.95 0l-.5-1.45a.5.5 0 0 0-.3-.3L9.45 12.1a.5.5 0 0 1 0-.95l1.45-.5a.5.5 0 0 0 .3-.3Z" />
  </Svg>
)

/** Mashq — yuguruvchi odam. */
export const RunIcon = (p) => (
  <Svg {...p}>
    <circle cx="14.6" cy="4.9" r="1.85" />
    <path d="M13.3 8.65 10.15 10.4a1.4 1.4 0 0 0-.62.7l-1.03 2.5" />
    <path d="M13.3 8.65a1.4 1.4 0 0 1 1.55.35l1.35 1.55a1.4 1.4 0 0 0 .7.43l2.35.6" />
    <path d="M13.55 12.7a1.4 1.4 0 0 1 .2 1.35l-1.1 2.5a1.4 1.4 0 0 1-.35.5l-3.2 2.9" />
    <path d="m12.35 16.5 2.5.95a1.4 1.4 0 0 1 .8.8l.9 2.1" />
  </Svg>
)
