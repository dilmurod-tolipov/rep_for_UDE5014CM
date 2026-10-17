# Secret — website

Flower bouquets (Secret), chocolate strawberries (Secret Berries) and houseplants (Green Mood), Tashkent.
React + Vite + Tailwind. No server: the finished site is a folder of plain files.

## Status: DEMO
The site shows a yellow "demo" bar, and the checkout and payment screens say no money is charged.
Orders are not sent anywhere and payments are simulated. Phone numbers are placeholders.
- To remove the demo labels later: set `DEMO_MODE = false` in `src/components/DemoNotice.tsx`
  (only once orders really reach the shop).
- To let Google find the site: remove the `<meta name="robots" ...>` line in `index.html`.

## Where things live
- Products (names, prices, descriptions in UZ/RU/EN): `src/data/products.ts`
  Prices there are PLACEHOLDERS until real prices are filled in.
- Product photos: `public/images/{flowers,berries,plants}/` (+ small copies in each `thumb/` folder)

## Admin panel (demo)
Open `/admin` (for example `http://localhost:3000/admin`). Demo password: `secret`.
- **Dashboard**: orders and revenue today, last 14 days chart, best sellers, orders by status.
- **Orders**: every order placed in the shop, filter by status, open one to see details,
  call the customer, move it along (new → confirmed → assembling → on the way → delivered) or cancel it.
- **Products**: change prices (tap the price), mark sold out, hide/show, edit names and texts in UZ/RU/EN,
  replace the photo, add or delete products.

Demo limits: data is stored **in this browser only** (localStorage). The shop and the admin on the
same computer share it, but other people see the original catalog. Sample orders are marked "demo".
"Reset demo data" in the admin puts everything back. The password is not real security.

## Moving to GCP later
All reading and saving goes through **`src/data/store.ts`**. Replace the bodies of its functions
(`getProducts`, `saveProduct`, `deleteProduct`, `getOrders`, `createOrder`, `updateOrder`) with calls
to your backend, for example a Cloud Run API with Firestore or Cloud SQL, photos in Cloud Storage,
and real admin sign-in with Firebase Auth / Identity Platform (replace `DEMO_PASSWORD` in
`src/admin/AdminApp.tsx`). The shop and admin screens do not need to change.
Then set `DEMO_MODE = false` in `src/components/DemoNotice.tsx`.

## Run on this computer
Double-click `start-secret-site.bat` (one folder up), or in this folder: `npm install --legacy-peer-deps` then `npm run dev`.

## Publish on Netlify (free)
1. Double-click `build-for-netlify.bat` (one folder up). It creates the `dist` folder.
2. Go to https://app.netlify.com/drop (free account, sign up with email or GitHub).
3. Drag the `dist` folder onto the page. The site is live in a few seconds.
4. To update later: run the .bat again, open the site in Netlify, **Deploys** tab, drag the new `dist` folder there.

Only `dist` is uploaded. Redirect and cache rules travel inside it (`public/_redirects`, `public/_headers`).
`netlify.toml` is for later, if the site is connected to GitHub for automatic deploys.
