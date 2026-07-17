---
version: alpha
name: Quiet Evidence
description: "Спокойная редакционная аналитика для писателя: сначала ответ, затем доказательство."
colors:
  primary: "#171714"
  secondary: "#625F57"
  accent: "#2F6B4F"
  accentSoft: "#E5F0E9"
  attention: "#9A5B24"
  attentionSoft: "#F7EBDD"
  neutral: "#F4F2ED"
  surface: "#FFFFFF"
  border: "#DCD8CF"
  focus: "#155EEF"
typography:
  h1:
    fontFamily: Inter
    fontSize: 2.5rem
    fontWeight: 650
    lineHeight: 1.08
    letterSpacing: "-0.035em"
  h2:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 620
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.04em"
  number:
    fontFamily: Inter
    fontSize: 1.75rem
    fontWeight: 650
    lineHeight: 1.1
rounded:
  sm: 6px
  md: 12px
  lg: 18px
  pill: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 16px
  badge-fact:
    backgroundColor: "{colors.accentSoft}"
    textColor: "{colors.accent}"
    rounded: "{rounded.pill}"
    padding: 6px
  badge-caution:
    backgroundColor: "{colors.attentionSoft}"
    textColor: "{colors.attention}"
    rounded: "{rounded.pill}"
    padding: 6px
---

## Overview

Quiet Evidence сочетает тёплую редакционную ясность Notion с точностью аналитических интерфейсов. Это не брендовый клон. Система берёт спокойные нейтрали, один зелёный цвет взаимодействия и прогрессивное раскрытие технических деталей.

## Colors

Фон тёплый, а карточки белые. Зелёный означает проверенный факт или безопасное действие. Охра отмечает ограничение данных, а не тревогу. Красный не используется для обычных отрицательных дельт: небольшое снижение не равно проблеме.

## Typography

Inter используется локально через системный fallback. Крупные заголовки короткие. Числа набираются табличными цифрами. Технические поля не получают отдельный визуальный стиль на первом уровне.

## Layout

Базовая сетка 8 px. Desktop имеет компактную боковую навигацию и рабочую область до 1120 px. Mobile использует нижнюю навигацию из четырёх пунктов. Первый viewport содержит ответ, период и не больше трёх объектов внимания.

## Elevation & Depth

Плоские поверхности и тонкие границы. Тени применяются только к плавающим деталям. Основная иерархия создаётся отступами, размером текста и фоном.

## Shapes

Радиусы умеренные: 6 px для действий, 12 px для карточек, 18 px для крупных областей. Pill применяется только к статусам и фильтрам.

## Components

- `DecisionBrief`: один ответ, период, уровень доказательности и кнопка раскрытия.
- `AttentionRow`: книга, причина показа, дельта и переход к evidence.
- `EvidenceDrawer`: исходные точки, формула, источник и ограничение вывода.
- `SparseState`: отдельные состояния для 0, 1 и 2+ точек.
- `SourceBadge`: человеческая подпись качества источника.
- `SectionNav`: Обзор, Книги, Топы, Читатели, Источники.

## Do's and Don'ts

- Показывать максимум три объекта внимания на обзоре.
- Писать "динамику считать рано", когда есть одна точка.
- Не соединять архивную и регулярную точки одной линией.
- Не показывать locator, source class или JSON до действия пользователя.
- Не окрашивать любую отрицательную дельту как ошибку.
- Не использовать английские технические подписи в основном интерфейсе.
