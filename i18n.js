// i18n helper — loads EN or VI based on user preference
const fs = require('fs');
const path = require('path');

const LOCALES = {
  en: JSON.parse(fs.readFileSync(path.join(__dirname, 'locales', 'en.json'), 'utf-8')),
  vi: JSON.parse(fs.readFileSync(path.join(__dirname, 'locales', 'vi.json'), 'utf-8')),
};

let currentLocale = 'en';

function setLocale(locale) {
  if (LOCALES[locale]) {
    currentLocale = locale;
  }
}

function t(key) {
  return LOCALES[currentLocale]?.[key] || LOCALES.en[key] || key;
}

function getLocale() {
  return currentLocale;
}

function getAvailableLocales() {
  return Object.keys(LOCALES);
}

module.exports = { t, setLocale, getLocale, getAvailableLocales };
