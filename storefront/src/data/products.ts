import { Product } from '../types';

// Real product photos live in /public/images. PRICES BELOW ARE PLACEHOLDERS: replace with real prices.
export const PRODUCTS: Product[] = [
  {
    id: "fl-01",
    brand: "secret_flowers",
    category: "hydrangeas",
    tags: ["hydrangea", "pastel", "gortenziya", "гортензия"],
    rating: 0,
    reviewsCount: 0,
    price: 1800000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/flowers/fl-01.jpg"],
    title: {"uz": "Pastel Gortenziyalar", "ru": "Пастельные гортензии", "en": "Pastel Hydrangea Dome"},
    subtitle: {"uz": "Pushti, binafsha, krem va yashil gortenziyalar", "ru": "Розовые, сиреневые, кремовые и зелёные гортензии", "en": "Pink, lilac, cream and green hydrangeas"},
    description: {"uz": "Turli rangdagi gortenziyalardan yig‘ilgan katta dumaloq guldasta, Secret lavanda tasmalari bilan bezatilgan.", "ru": "Большой круглый букет из гортензий разных оттенков, перевязанный лавандовыми лентами Secret.", "en": "A large round bouquet of hydrangeas in many soft shades, wrapped in lavender Secret ribbons."},
    composition: {"uz": ["Pushti, binafsha, krem va yashil gortenziyalar", "Evkalipt", "Secret lavanda tasmalari"], "ru": ["Гортензии: розовые, сиреневые, кремовые, зелёные", "Эвкалипт", "Лавандовые ленты Secret"], "en": ["Pink, lilac, cream and green hydrangeas", "Eucalyptus", "Lavender Secret ribbons"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-02",
    brand: "secret_flowers",
    category: "orchids",
    tags: ["orchid", "hydrangea", "orxideya", "орхидея"],
    rating: 0,
    reviewsCount: 0,
    price: 2200000, // PLACEHOLDER
    prepTimeMinutes: 75,
    dimensions: '',
    images: ["/images/flowers/fl-02.jpg"],
    title: {"uz": "Orxideya va Osmon", "ru": "Орхидеи и небо", "en": "Orchid Sky"},
    subtitle: {"uz": "Pushti orxideyalar, havorang gortenziya va shaftoli atirgullar", "ru": "Розовые орхидеи, голубая гортензия и персиковые розы", "en": "Pink orchids, blue hydrangea and peach roses"},
    description: {"uz": "Havorang va pushti gortenziyalar ustida pushti orxideyalar, shaftoli rang atirgullar va krem xrizantemalar.", "ru": "Розовые орхидеи на облаке из голубых и розовых гортензий, с персиковыми розами и кремовыми хризантемами.", "en": "Pink orchids resting on a cloud of blue and pink hydrangeas, with peach roses and cream pompon chrysanthemums."},
    composition: {"uz": ["Pushti orxideyalar", "Havorang va pushti gortenziyalar", "Shaftoli atirgullar", "Krem xrizantemalar", "Secret tasmalari"], "ru": ["Розовые орхидеи", "Голубые и розовые гортензии", "Персиковые розы", "Кремовые хризантемы", "Ленты Secret"], "en": ["Pink orchids", "Blue and pink hydrangeas", "Peach roses", "Cream pompon chrysanthemums", "Secret ribbons"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-03",
    brand: "secret_flowers",
    category: "hydrangeas",
    tags: ["hydrangea", "roses", "cream", "гортензия"],
    rating: 0,
    reviewsCount: 0,
    price: 1900000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/flowers/fl-03.jpg"],
    title: {"uz": "Pushti Krem", "ru": "Розовый крем", "en": "Blush & Cream"},
    subtitle: {"uz": "Pushti gortenziya, krem atirgullar va oq eustomalar", "ru": "Розовая гортензия, кремовые розы и белые эустомы", "en": "Pink hydrangea, cream roses and white lisianthus"},
    description: {"uz": "Nozik pushti gortenziyalar ichida krem atirgullar, oq eustomalar va krem xrizantemalar.", "ru": "Нежные розовые гортензии с кремовыми розами, белыми эустомами и кремовыми хризантемами.", "en": "Soft pink hydrangeas dotted with cream roses, white lisianthus and cream pompon chrysanthemums."},
    composition: {"uz": ["Pushti gortenziyalar", "Krem atirgullar", "Oq eustomalar", "Krem xrizantemalar", "Evkalipt", "Secret tasmalari"], "ru": ["Розовые гортензии", "Кремовые розы", "Белые эустомы", "Кремовые хризантемы", "Эвкалипт", "Ленты Secret"], "en": ["Pink hydrangeas", "Cream roses", "White lisianthus", "Cream pompon chrysanthemums", "Eucalyptus", "Secret ribbons"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-04",
    brand: "secret_flowers",
    category: "hydrangeas",
    tags: ["hydrangea", "roses", "fuchsia", "гортензия"],
    rating: 0,
    reviewsCount: 0,
    price: 1900000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/flowers/fl-04.jpg"],
    title: {"uz": "Pushti va Fuksiya", "ru": "Розовый и фуксия", "en": "Blush & Fuchsia"},
    subtitle: {"uz": "Pushti gortenziya, fuksiya pionsimon atirgullar", "ru": "Розовая гортензия и пионовидные розы цвета фуксии", "en": "Pink hydrangea with fuchsia peony roses"},
    description: {"uz": "Pushti gortenziyalar orasida yorqin fuksiya pionsimon atirgullar va oq eustomalar.", "ru": "Розовые гортензии с яркими пионовидными розами цвета фуксии и белыми эустомами.", "en": "Pink hydrangeas lit up with bright fuchsia peony roses and white lisianthus."},
    composition: {"uz": ["Pushti gortenziyalar", "Fuksiya pionsimon atirgullar", "Oq eustomalar", "Evkalipt", "Secret tasmalari"], "ru": ["Розовые гортензии", "Пионовидные розы фуксия", "Белые эустомы", "Эвкалипт", "Ленты Secret"], "en": ["Pink hydrangeas", "Fuchsia peony roses", "White lisianthus", "Eucalyptus", "Secret ribbons"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-05",
    brand: "secret_flowers",
    category: "roses",
    tags: ["roses", "spray roses", "atirgul", "розы"],
    rating: 0,
    reviewsCount: 0,
    price: 2500000, // PLACEHOLDER
    prepTimeMinutes: 75,
    dimensions: '',
    images: ["/images/flowers/fl-05.jpg"],
    title: {"uz": "Fuksiya Atirgullar", "ru": "Розы фуксия", "en": "Fuchsia Spray Roses"},
    subtitle: {"uz": "Yuzlab fuksiya pionsimon butasimon atirgullar", "ru": "Сотни пионовидных кустовых роз цвета фуксии", "en": "Hundreds of fuchsia peony spray roses"},
    description: {"uz": "Faqat fuksiya rangli pionsimon butasimon atirgullardan iborat katta dumaloq guldasta.", "ru": "Большой круглый букет только из пионовидных кустовых роз цвета фуксии.", "en": "A large round bouquet made only of fuchsia peony spray roses."},
    composition: {"uz": ["Fuksiya pionsimon butasimon atirgullar", "Secret logotipi"], "ru": ["Пионовидные кустовые розы фуксия", "Логотип Secret"], "en": ["Fuchsia peony spray roses", "Secret logo pin"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-06",
    brand: "secret_flowers",
    category: "mixed",
    tags: ["hydrangea", "tulips", "lilac", "тюльпаны"],
    rating: 0,
    reviewsCount: 0,
    price: 2100000, // PLACEHOLDER
    prepTimeMinutes: 75,
    dimensions: '',
    images: ["/images/flowers/fl-06.jpg"],
    title: {"uz": "Lavanda Bog‘i", "ru": "Лавандовый сад", "en": "Lavender Garden"},
    subtitle: {"uz": "Binafsha gortenziya, lolalar va pushti xrizantemalar", "ru": "Сиреневая гортензия, тюльпаны и розовые хризантемы", "en": "Lilac hydrangea, tulips and pink chrysanthemums"},
    description: {"uz": "Binafsha gortenziyalar ustida shaftoli lolalar, pushti xrizantemalar va eustomalar, lavanda Secret tasmalari bilan.", "ru": "Сиреневые гортензии с персиковыми тюльпанами, розовыми хризантемами и эустомами, в лавандовых лентах Secret.", "en": "Lilac hydrangeas with peach tulips, pink pompon chrysanthemums and lisianthus, in lavender Secret ribbons."},
    composition: {"uz": ["Binafsha gortenziyalar", "Shaftoli lolalar", "Pushti xrizantemalar", "Pushti eustomalar", "Astilba", "Secret tasmalari"], "ru": ["Сиреневые гортензии", "Персиковые тюльпаны", "Розовые хризантемы", "Розовые эустомы", "Астильба", "Ленты Secret"], "en": ["Lilac hydrangeas", "Peach tulips", "Pink pompon chrysanthemums", "Pink lisianthus", "Astilbe", "Secret ribbons"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-07",
    brand: "secret_flowers",
    category: "orchids",
    tags: ["orchid", "hydrangea", "white", "орхидея"],
    rating: 0,
    reviewsCount: 0,
    price: 2300000, // PLACEHOLDER
    prepTimeMinutes: 75,
    dimensions: '',
    images: ["/images/flowers/fl-07.jpg"],
    title: {"uz": "Oq Orxideya", "ru": "Белая орхидея", "en": "White Orchid Blush"},
    subtitle: {"uz": "Pushti gortenziya, oq orxideyalar va krem atirgullar", "ru": "Розовая гортензия, белые орхидеи и кремовые розы", "en": "Pink hydrangea, white orchids and cream roses"},
    description: {"uz": "Pushti gortenziyalar ichida oq orxideyalar va krem pionsimon atirgullar.", "ru": "Розовые гортензии с белыми орхидеями и кремовыми пионовидными розами.", "en": "Pink hydrangeas with white orchids and cream peony roses."},
    composition: {"uz": ["Pushti gortenziyalar", "Oq orxideyalar", "Krem pionsimon atirgullar", "Evkalipt", "Secret logotipi"], "ru": ["Розовые гортензии", "Белые орхидеи", "Кремовые пионовидные розы", "Эвкалипт", "Логотип Secret"], "en": ["Pink hydrangeas", "White orchids", "Cream peony roses", "Eucalyptus", "Secret logo pin"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "fl-08",
    brand: "secret_flowers",
    category: "roses",
    tags: ["roses", "spray roses", "pink", "розы"],
    rating: 0,
    reviewsCount: 0,
    price: 2400000, // PLACEHOLDER
    prepTimeMinutes: 75,
    dimensions: '',
    images: ["/images/flowers/fl-08.jpg"],
    title: {"uz": "Pushti Atirgullar Miksi", "ru": "Микс розовых роз", "en": "Pink Rose Medley"},
    subtitle: {"uz": "Pushtining turli tuslaridagi butasimon atirgullar", "ru": "Кустовые розы в разных оттенках розового", "en": "Spray roses in every shade of pink"},
    description: {"uz": "Oqish pushtidan to fuksiyagacha bo‘lgan atirgullardan yig‘ilgan katta guldasta.", "ru": "Большой букет из роз от пудрово-розового до фуксии.", "en": "A large bouquet of roses running from pale blush to deep fuchsia."},
    composition: {"uz": ["Pushti, oqish va fuksiya butasimon atirgullar", "Secret logotipi"], "ru": ["Кустовые розы: розовые, пудровые, фуксия", "Логотип Secret"], "en": ["Blush, pink and fuchsia spray roses", "Secret logo pin"]},
    careTips: {"uz": ["Har kuni gubkaga 150 ml sovuq suv quying", "To‘g‘ridan-to‘g‘ri quyosh va isitgichdan uzoqroq tuting", "Salqin xonada saqlang"], "ru": ["Ежедневно подливайте 150 мл холодной воды в губку", "Берегите от прямого солнца и батарей", "Храните в прохладной комнате"], "en": ["Add 150 ml of cold water to the floral sponge daily", "Keep away from direct sun and heaters", "Keep in a cool room"]}
  },
  {
    id: "sb-01",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "chocolate", "box", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 550000, // PLACEHOLDER
    prepTimeMinutes: 45,
    dimensions: '',
    images: ["/images/berries/sb-01.jpg"],
    title: {"uz": "Qora Quti", "ru": "Чёрная коробка", "en": "Noir Window Box"},
    subtitle: {"uz": "Sut shokoladidagi qulupnaylar, qora oynali qutida", "ru": "Клубника в молочном шоколаде в чёрной коробке с окном", "en": "Milk chocolate strawberries in a black window box"},
    description: {"uz": "Sut shokoladiga botirilgan qulupnaylar, oltin Secret yozuvli qora tasma bilan bog‘langan qora qutida.", "ru": "Клубника в молочном шоколаде в чёрной коробке, перевязанной чёрной лентой с золотым логотипом Secret.", "en": "Strawberries dipped in milk chocolate, in a black box tied with a black ribbon with gold Secret lettering."},
    composition: {"uz": ["Sut shokoladidagi qulupnaylar", "Oynali qora quti", "Oltin yozuvli Secret tasmasi"], "ru": ["Клубника в молочном шоколаде", "Чёрная коробка с окном", "Лента Secret с золотым тиснением"], "en": ["Milk chocolate strawberries", "Black window box", "Secret ribbon with gold lettering"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-02",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "assorted", "pistachio", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 850000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/berries/sb-02.jpg"],
    title: {"uz": "Rangli Assorti", "ru": "Цветное ассорти", "en": "Colour Assortment"},
    subtitle: {"uz": "Qulupnaylar va rangli rezavorlar, dumaloq bordo qutida", "ru": "Клубника и цветные ягоды в круглой бордовой коробке", "en": "Strawberries and coloured berries in a round burgundy box"},
    description: {"uz": "Shokoladdagi qulupnaylar, rangli glazurdagi rezavorlar, pista va ko‘k meva bilan dumaloq bordo Secret qutisi.", "ru": "Круглая бордовая коробка Secret: клубника в шоколаде, ягоды в цветной глазури, фисташка и голубика.", "en": "A round burgundy Secret box of chocolate strawberries, berries in coloured glaze, pistachio and blueberries."},
    composition: {"uz": ["Shokoladdagi qulupnaylar", "Rangli glazurdagi rezavorlar", "Pista", "Ko‘k meva", "Dumaloq bordo quti"], "ru": ["Клубника в шоколаде", "Ягоды в цветной глазури", "Фисташка", "Голубика", "Круглая бордовая коробка"], "en": ["Chocolate strawberries", "Berries in coloured glaze", "Pistachio", "Blueberries", "Round burgundy box"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-03",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "chocolate", "blueberry", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 750000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/berries/sb-03.jpg"],
    title: {"uz": "Klassik Dumaloq Quti", "ru": "Классическая круглая коробка", "en": "Classic Round Box"},
    subtitle: {"uz": "Sut shokoladidagi qulupnaylar va ko‘k meva", "ru": "Клубника в молочном шоколаде и голубика", "en": "Milk chocolate strawberries with blueberries"},
    description: {"uz": "Chiziqli bezakli sut shokoladidagi qulupnaylar va yangi ko‘k meva, dumaloq bordo Secret qutisida.", "ru": "Клубника в молочном шоколаде с тонкими полосками и свежая голубика в круглой бордовой коробке Secret.", "en": "Striped milk chocolate strawberries with fresh blueberries in a round burgundy Secret box."},
    composition: {"uz": ["Sut shokoladidagi qulupnaylar", "Ko‘k meva", "Dumaloq bordo quti"], "ru": ["Клубника в молочном шоколаде", "Голубика", "Круглая бордовая коробка"], "en": ["Milk chocolate strawberries", "Blueberries", "Round burgundy box"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-04",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "heart", "gold", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 700000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/berries/sb-04.jpg"],
    title: {"uz": "Oltin Yurak", "ru": "Золотое сердце", "en": "Golden Heart"},
    subtitle: {"uz": "Oltin bargli qulupnaylar, yurak shaklidagi qutida", "ru": "Клубника с золотой поталью в коробке-сердце", "en": "Gold-leaf strawberries in a heart box"},
    description: {"uz": "Oltin barg bilan bezatilgan shokoladdagi qulupnaylar va ko‘k meva, bordo yurak shaklidagi qutida.", "ru": "Клубника в шоколаде с золотой поталью и голубика в бордовой коробке-сердце.", "en": "Chocolate strawberries finished with gold leaf, with blueberries, in a burgundy heart-shaped box."},
    composition: {"uz": ["Shokoladdagi qulupnaylar", "Oltin barg", "Ko‘k meva", "Yurak shaklidagi bordo quti"], "ru": ["Клубника в шоколаде", "Золотая поталь", "Голубика", "Бордовая коробка-сердце"], "en": ["Chocolate strawberries", "Gold leaf", "Blueberries", "Burgundy heart box"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-05",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "white chocolate", "assorted", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 900000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/berries/sb-05.jpg"],
    title: {"uz": "Katta Assorti Quti", "ru": "Большое ассорти", "en": "Grand Assortment Box"},
    subtitle: {"uz": "Oq va sut shokoladi, yong‘oq sepilgan qulupnaylar", "ru": "Клубника в белом и молочном шоколаде, с орехами", "en": "White and milk chocolate strawberries with nut toppings"},
    description: {"uz": "Oq va sut shokoladidagi, yong‘oq va oltin bilan bezatilgan qulupnaylar, oynali bordo qutida.", "ru": "Клубника в белом и молочном шоколаде, с орехами и золотом, в бордовой коробке с окном.", "en": "Strawberries in white and milk chocolate, topped with nuts and gold, in a burgundy window box."},
    composition: {"uz": ["Oq shokoladdagi qulupnaylar", "Sut shokoladidagi qulupnaylar", "Yong‘oq sepilgan qulupnaylar", "Oynali bordo quti"], "ru": ["Клубника в белом шоколаде", "Клубника в молочном шоколаде", "Клубника с орехами", "Бордовая коробка с окном"], "en": ["White chocolate strawberries", "Milk chocolate strawberries", "Nut-topped strawberries", "Burgundy window box"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-06",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "pistachio", "heart", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 450000, // PLACEHOLDER
    prepTimeMinutes: 45,
    dimensions: '',
    images: ["/images/berries/sb-06.jpg"],
    title: {"uz": "Qora Yurak", "ru": "Чёрное сердце", "en": "Noir Heart"},
    subtitle: {"uz": "Pista va yong‘oqli qulupnaylar, qora yurak qutida", "ru": "Клубника с фисташкой и орехами в чёрном сердце", "en": "Pistachio and nut strawberries in a black heart box"},
    description: {"uz": "Pista va yong‘oq sepilgan shokoladdagi qulupnaylar, kichik qora yurak shaklidagi Secret qutisida.", "ru": "Клубника в шоколаде с фисташкой и орехами в небольшой чёрной коробке-сердце Secret.", "en": "Chocolate strawberries topped with pistachio and nuts in a small black Secret heart box."},
    composition: {"uz": ["Shokoladdagi qulupnaylar", "Pista", "Yong‘oq", "Qora yurak shaklidagi quti"], "ru": ["Клубника в шоколаде", "Фисташка", "Орехи", "Чёрная коробка-сердце"], "en": ["Chocolate strawberries", "Pistachio", "Nuts", "Black heart box"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "sb-07",
    brand: "secret_berries",
    category: "strawberries",
    tags: ["strawberry", "butterfly", "gift", "клубника"],
    rating: 0,
    reviewsCount: 0,
    price: 650000, // PLACEHOLDER
    prepTimeMinutes: 60,
    dimensions: '',
    images: ["/images/berries/sb-07.jpg"],
    title: {"uz": "Kapalak", "ru": "Бабочка", "en": "Butterfly Box"},
    subtitle: {"uz": "Kapalak shaklidagi qutida shokoladdagi qulupnaylar", "ru": "Клубника в шоколаде в коробке-бабочке", "en": "Chocolate strawberries in a butterfly box"},
    description: {"uz": "Sut shokoladidagi qulupnaylar, shaffof qopqoqli oq kapalak shaklidagi qutida, Secret tasmasi bilan.", "ru": "Клубника в молочном шоколаде в белой коробке-бабочке с прозрачной крышкой и лентой Secret.", "en": "Milk chocolate strawberries in a white butterfly-shaped box with a clear lid and a Secret ribbon."},
    composition: {"uz": ["Sut shokoladidagi qulupnaylar", "Kapalak shaklidagi oq quti", "Secret tasmasi"], "ru": ["Клубника в молочном шоколаде", "Белая коробка-бабочка", "Лента Secret"], "en": ["Milk chocolate strawberries", "White butterfly box", "Secret ribbon"]},
    careTips: {"uz": ["Muzlatgichda +2…+6 °C da saqlang", "Yetkazilgan kuni iste’mol qilish tavsiya etiladi", "Iste’moldan 10 daqiqa oldin chiqarib qo‘ying"], "ru": ["Храните в холодильнике при +2…+6 °C", "Лучше всего съесть в день доставки", "Достаньте за 10 минут до подачи"], "en": ["Keep refrigerated at +2 to +6 °C", "Best enjoyed on the day of delivery", "Take out 10 minutes before serving"]}
  },
  {
    id: "gm-01",
    brand: "green_mood",
    category: "houseplants",
    tags: ["bamboo", "lucky bamboo", "bambuk", "бамбук"],
    rating: 0,
    reviewsCount: 0,
    price: 350000, // PLACEHOLDER
    prepTimeMinutes: 20,
    dimensions: '',
    images: ["/images/plants/gm-01.jpg"],
    title: {"uz": "Baxt Bambugi", "ru": "Бамбук удачи", "en": "Lucky Bamboo Pair"},
    subtitle: {"uz": "Ikki spiral poyali dekorativ bambuk", "ru": "Пара декоративных спиральных бамбуков", "en": "Two spiral-stem lucky bamboo plants"},
    description: {"uz": "Spiral shaklidagi ikki dekorativ bambuk, uy va ofis uchun.", "ru": "Два декоративных бамбука со спиральными стеблями для дома и офиса.", "en": "Two decorative lucky bamboo plants with spiral stems, for home or office."},
    composition: {"uz": ["2 ta spiral bambuk (Dracaena sanderiana)"], "ru": ["2 спиральных бамбука (Dracaena sanderiana)"], "en": ["2 spiral lucky bamboo (Dracaena sanderiana)"]},
    careTips: {"uz": ["Tuproq yuzasi qurigandagina sug‘oring", "Yorug‘, lekin to‘g‘ridan-to‘g‘ri quyosh tushmaydigan joyga qo‘ying", "Barglarni vaqti-vaqti bilan nam latta bilan arting"], "ru": ["Поливайте, когда верхний слой почвы подсохнет", "Светлое место без прямого солнца", "Время от времени протирайте листья влажной тканью"], "en": ["Water when the top of the soil is dry", "Bright spot out of direct sun", "Wipe the leaves with a damp cloth now and then"]}
  },
  {
    id: "gm-02",
    brand: "green_mood",
    category: "houseplants",
    tags: ["dracaena", "plant", "драцена"],
    rating: 0,
    reviewsCount: 0,
    price: 650000, // PLACEHOLDER
    prepTimeMinutes: 20,
    dimensions: '',
    images: ["/images/plants/gm-02.jpg"],
    title: {"uz": "Dratsena", "ru": "Драцена", "en": "Dracaena"},
    subtitle: {"uz": "Oq baland tuvakdagi dratsena", "ru": "Драцена в высоком белом кашпо", "en": "Dracaena in a tall white pot"},
    description: {"uz": "Yashil-sariq barglari bilan yorqin dratsena, oq baland tuvakda.", "ru": "Яркая драцена с жёлто-зелёными листьями в высоком белом кашпо.", "en": "A bright dracaena with yellow-green leaves in a tall white pot."},
    composition: {"uz": ["Dratsena", "Oq baland tuvak"], "ru": ["Драцена", "Высокое белое кашпо"], "en": ["Dracaena", "Tall white pot"]},
    careTips: {"uz": ["Tuproq yuzasi qurigandagina sug‘oring", "Yorug‘, lekin to‘g‘ridan-to‘g‘ri quyosh tushmaydigan joyga qo‘ying", "Barglarni vaqti-vaqti bilan nam latta bilan arting"], "ru": ["Поливайте, когда верхний слой почвы подсохнет", "Светлое место без прямого солнца", "Время от времени протирайте листья влажной тканью"], "en": ["Water when the top of the soil is dry", "Bright spot out of direct sun", "Wipe the leaves with a damp cloth now and then"]}
  },
  {
    id: "gm-03",
    brand: "green_mood",
    category: "trees",
    tags: ["tree", "plant", "дерево"],
    rating: 0,
    reviewsCount: 0,
    price: 900000, // PLACEHOLDER
    prepTimeMinutes: 20,
    dimensions: '',
    images: ["/images/plants/gm-03.jpg"],
    title: {"uz": "Yashil Toj Daraxti", "ru": "Дерево «Зелёная крона»", "en": "Green Crown Tree"},
    subtitle: {"uz": "Oq baland tuvakdagi qalin bargli daraxt", "ru": "Дерево с густой кроной в высоком белом кашпо", "en": "A leafy standard tree in a tall white pot"},
    description: {"uz": "Qalin, yaltiroq yashil tojli uy daraxti, oq baland tuvakda. Ofis va mehmonxona uchun.", "ru": "Комнатное дерево с густой глянцевой кроной в высоком белом кашпо. Для офиса и гостиной.", "en": "An indoor tree with a dense, glossy green crown in a tall white pot. Made for offices and living rooms."},
    composition: {"uz": ["Uy daraxti", "Oq baland tuvak"], "ru": ["Комнатное дерево", "Высокое белое кашпо"], "en": ["Indoor tree", "Tall white pot"]},
    careTips: {"uz": ["Tuproq yuzasi qurigandagina sug‘oring", "Yorug‘, lekin to‘g‘ridan-to‘g‘ri quyosh tushmaydigan joyga qo‘ying", "Barglarni vaqti-vaqti bilan nam latta bilan arting"], "ru": ["Поливайте, когда верхний слой почвы подсохнет", "Светлое место без прямого солнца", "Время от времени протирайте листья влажной тканью"], "en": ["Water when the top of the soil is dry", "Bright spot out of direct sun", "Wipe the leaves with a damp cloth now and then"]}
  },
  {
    id: "gm-04",
    brand: "green_mood",
    category: "palms",
    tags: ["palm", "areca", "пальма"],
    rating: 0,
    reviewsCount: 0,
    price: 950000, // PLACEHOLDER
    prepTimeMinutes: 20,
    dimensions: '',
    images: ["/images/plants/gm-04.jpg"],
    title: {"uz": "Areka Palmasi", "ru": "Пальма Арека", "en": "Areca Palm"},
    subtitle: {"uz": "Oq baland tuvakdagi areka palmasi", "ru": "Пальма арека в высоком белом кашпо", "en": "Areca palm in a tall white pot"},
    description: {"uz": "Yengil, patsimon barglari bilan baland areka palmasi, oq tuvakda.", "ru": "Высокая пальма арека с лёгкими перистыми листьями в белом кашпо.", "en": "A tall areca palm with light, feathery fronds in a white pot."},
    composition: {"uz": ["Areka palmasi (Dypsis lutescens)", "Oq baland tuvak"], "ru": ["Пальма арека (Dypsis lutescens)", "Высокое белое кашпо"], "en": ["Areca palm (Dypsis lutescens)", "Tall white pot"]},
    careTips: {"uz": ["Tuproq yuzasi qurigandagina sug‘oring", "Yorug‘, lekin to‘g‘ridan-to‘g‘ri quyosh tushmaydigan joyga qo‘ying", "Barglarni vaqti-vaqti bilan nam latta bilan arting"], "ru": ["Поливайте, когда верхний слой почвы подсохнет", "Светлое место без прямого солнца", "Время от времени протирайте листья влажной тканью"], "en": ["Water when the top of the soil is dry", "Bright spot out of direct sun", "Wipe the leaves with a damp cloth now and then"]}
  },
  {
    id: "gm-05",
    brand: "green_mood",
    category: "houseplants",
    tags: ["zz plant", "zamioculcas", "замиокулькас"],
    rating: 0,
    reviewsCount: 0,
    price: 600000, // PLACEHOLDER
    prepTimeMinutes: 20,
    dimensions: '',
    images: ["/images/plants/gm-05.jpg"],
    title: {"uz": "Zamiokulkas", "ru": "Замиокулькас", "en": "ZZ Plant"},
    subtitle: {"uz": "Oq baland tuvakdagi zamiokulkas", "ru": "Замиокулькас в высоком белом кашпо", "en": "ZZ plant in a tall white pot"},
    description: {"uz": "Parvarishi oson, to‘q yashil yaltiroq bargli zamiokulkas, oq tuvakda.", "ru": "Неприхотливый замиокулькас с тёмно-зелёными глянцевыми листьями в белом кашпо.", "en": "An easy-care ZZ plant with dark, glossy leaves in a white pot."},
    composition: {"uz": ["Zamiokulkas (Zamioculcas zamiifolia)", "Oq baland tuvak"], "ru": ["Замиокулькас (Zamioculcas zamiifolia)", "Высокое белое кашпо"], "en": ["ZZ plant (Zamioculcas zamiifolia)", "Tall white pot"]},
    careTips: {"uz": ["Tuproq yuzasi qurigandagina sug‘oring", "Yorug‘, lekin to‘g‘ridan-to‘g‘ri quyosh tushmaydigan joyga qo‘ying", "Barglarni vaqti-vaqti bilan nam latta bilan arting"], "ru": ["Поливайте, когда верхний слой почвы подсохнет", "Светлое место без прямого солнца", "Время от времени протирайте листья влажной тканью"], "en": ["Water when the top of the soil is dry", "Bright spot out of direct sun", "Wipe the leaves with a damp cloth now and then"]}
  }
];

export const ADDONS_CATALOG = [
  {
    id: 'addon-vase',
    name: {
      uz: 'Kristal Shisha Vaza "Parisian Cylindre"',
      ru: 'Хрустальная ваза "Parisian Cylindre"',
      en: 'Crystal Glass Vase "Parisian Cylindre"'
    },
    price: 180000,
    image: 'https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'addon-candle',
    name: {
      uz: 'Tabiiy Soya Shami "French Peony & Amber"',
      ru: 'Ароматическая соевая свеча "French Peony & Amber"',
      en: 'Natural Soy Candle "French Peony & Amber"'
    },
    price: 140000,
    image: 'https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'addon-choc',
    name: {
      uz: 'Callebaut Belgiya Qo‘lbola Shokoladi (100g)',
      ru: 'Ремесленный бельгийский шоколад Callebaut (100г)',
      en: 'Artisan Callebaut Belgian Chocolate Bar (100g)'
    },
    price: 95000,
    image: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'addon-teddy',
    name: {
      uz: 'Maxsus Yumshoq Ayiqcha "Secret Mini Teddy"',
      ru: 'Плюшевый мишка "Secret Mini Teddy"',
      en: 'Plush Artisan Teddy Bear "Secret Mini Teddy"'
    },
    price: 160000,
    image: 'https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=400&q=80'
  }
];

export const TASHKENT_DISTRICTS = [
  'Mirzo Ulug‘bek tumani',
  'Yunusobod tumani',
  'Yakkasaroy tumani',
  'Mirobod tumani',
  'Shayxontohur tumani',
  'Chilonzor tumani',
  'Uchtepa tumani',
  'Yashnobod tumani',
  'Olmazor tumani',
  'Sergeli tumani',
  'Bektemir tumani',
  'Yangihayot tumani'
];

export const INITIAL_COURIERS: import('../types').CourierInfo[] = [
  {
    id: 'cour-01',
    name: 'Sardor Rahimov',
    phone: '+998 90 123 45 67',
    vehicle: 'Chevrolet Tracker (Termo-bort)',
    status: 'available',
    rating: 4.98,
    activeOrders: 1
  },
  {
    id: 'cour-02',
    name: 'Javohir Alimov',
    phone: '+998 93 987 65 43',
    vehicle: 'Chevrolet Cobalt (Konditsionerli)',
    status: 'delivering',
    rating: 4.95,
    activeOrders: 2
  },
  {
    id: 'cour-03',
    name: 'Dilshod Karimov',
    phone: '+998 97 555 11 22',
    vehicle: 'Express Moto Termo-box',
    status: 'available',
    rating: 4.92,
    activeOrders: 0
  }
];

export const INITIAL_ORDERS: import('../types').Order[] = [
  {
    id: 'ord-101',
    orderNumber: 'SEC-8924',
    createdAt: '2026-09-20T13:45:00',
    brand: 'secret_flowers',
    items: [
      {
        productId: 'fl-03',
        productTitle: {
          uz: 'Royal Peony Whisper — Marvarid Pion Guldastasi',
          ru: 'Royal Peony Whisper — Шляпная коробка с пионами',
          en: 'Royal Peony Whisper — Luxury Peony Hatbox'
        },
        productImage: '/images/flowers/thumb/fl-03.jpg',
        quantity: 1,
        price: 1250000,
        brand: 'secret_flowers',
        cardMessage: 'Tug‘ilgan kuningiz muborak bo‘lsin, go‘zalim! Siz dunyodagi eng ajoyibsiz ❤️'
      }
    ],
    customer: {
      name: 'Aziz Mahmudov',
      phone: '+998 90 999 88 77',
      email: 'aziz.m@gmail.com'
    },
    recipient: {
      isRecipientCustomer: false,
      name: 'Madina Karimova',
      phone: '+998 91 222 33 44',
      isSurprise: true
    },
    delivery: {
      district: 'Mirobod tumani',
      address: 'Chexov ko‘chasi, 24-uy',
      apartment: '34-xonadon',
      landmark: 'Grand Mir Hotel orqasi',
      date: 'Bugun (20-Sentabr)',
      timeSlot: '16:00 - 18:00',
      type: 'scheduled'
    },
    cardMessage: 'Tug‘ilgan kuningiz muborak bo‘lsin, go‘zalim! Siz dunyodagi eng ajoyibsiz ❤️',
    payment: {
      method: 'payme',
      status: 'paid',
      transactionId: 'PAYME-98214-UZ',
      paidAt: '2026-09-20T13:46:12'
    },
    status: 'assembling',
    subtotal: 1250000,
    deliveryFee: 35000,
    discount: 0,
    total: 1285000,
    courier: {
      id: 'cour-01',
      name: 'Sardor Rahimov',
      phone: '+998 90 123 45 67',
      assignedAt: '13:50',
      etaMinutes: 45,
      vehicle: 'Chevrolet Tracker (Termo-bort)'
    },
    qualityCheckPhoto: '/images/flowers/thumb/fl-03.jpg',
    notes: 'Kuryer eshik qo‘ng‘irog‘ini chalmasin, avval telefon qilsin.'
  },
  {
    id: 'ord-102',
    orderNumber: 'SEC-8925',
    createdAt: '2026-09-20T14:10:00',
    brand: 'secret_berries',
    items: [
      {
        productId: 'sb-01',
        productTitle: {
          uz: 'Ruby Noir Grand Box — Belgiya Shokoladli Qulupnaylar',
          ru: 'Ruby Noir Grand Box — Клубника в бельгийском шоколаде Callebaut',
          en: 'Ruby Noir Grand Box — Belgian Callebaut Chocolate Strawberries'
        },
        productImage: '/images/berries/thumb/sb-03.jpg',
        quantity: 1,
        price: 490000,
        brand: 'secret_berries'
      }
    ],
    customer: {
      name: 'Kamila Rustamova',
      phone: '+998 93 456 78 90'
    },
    recipient: {
      isRecipientCustomer: true,
      name: 'Kamila Rustamova',
      phone: '+998 93 456 78 90',
      isSurprise: false
    },
    delivery: {
      district: 'Yunusobod tumani',
      address: 'Amir Temur shoh ko‘chasi, 108',
      apartment: 'Ofis 502',
      landmark: 'Shahriston metrosi yaqinida',
      date: 'Bugun (20-Sentabr)',
      timeSlot: 'Ekspress (60 daqiqa)',
      type: 'express'
    },
    payment: {
      method: 'click',
      status: 'paid',
      transactionId: 'CLICK-77621-UZ',
      paidAt: '2026-09-20T14:11:05'
    },
    status: 'in_transit',
    subtotal: 490000,
    deliveryFee: 40000,
    discount: 0,
    total: 530000,
    courier: {
      id: 'cour-02',
      name: 'Javohir Alimov',
      phone: '+998 93 987 65 43',
      assignedAt: '14:15',
      etaMinutes: 20,
      vehicle: 'Chevrolet Cobalt (Konditsionerli)'
    }
  }
];
