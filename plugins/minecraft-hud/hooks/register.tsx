import type { Register, SessionUsage } from 'claude-code'

import { DIGITS, SPRITES } from './sprites'

const W = 182
const MAX_SCALE = 6
const PX_PER_COLUMN = 7.8 // advance of the desktop's code font; ~98.5% of the band is used so it never overflows

// Remaining capacity in half-units (0..20) from a percent used; any remainder shows at least half a unit.
// No reading yet (before the first API response) draws full, never empty.
const points = (used: number | undefined) => {
  if (used === undefined) return 20
  const left = Math.max(0, 100 - used)
  return left <= 0 ? 0 : Math.max(1, Math.round(left / 5))
}

const sprite = (name: string, x: number, y: number) => {
  const s = SPRITES[name]
  return `<g transform="translate(${x} ${y})">${s.p.map(([c, d]) => `<path fill="${c}" d="${d}"/>`).join('')}</g>`
}

const ROW_W = 81 // ten icons, 8 apart, the last 9 wide

const iconRow = (kind: 'heart' | 'food', pts: number, rtl: boolean) => {
  let out = ''
  for (let i = 0; i < 10; i++) {
    const x = rtl ? ROW_W - 9 - i * 8 : i * 8
    const left = pts - i * 2
    if (kind === 'heart') out += sprite('heart_container', x, 0)
    if (left >= 1 || kind !== 'heart') out += sprite(left >= 2 ? `${kind}_full` : left === 1 ? `${kind}_half` : `${kind}_empty`, x, 0)
  }
  return out
}

const MID_W = W - 2 * ROW_W // 20: the gap between hearts and hunger, where the level sits

const levelText = (n: number) => {
  const digits = String(n).split('')
  const width = digits.reduce((w, c) => w + DIGITS[c].w + 1, -1)
  let x = Math.round((MID_W - width) / 2)
  let d = ''
  for (const c of digits) {
    d += `<path transform="translate(${x} 2)" d="${DIGITS[c].d}"/>`
    x += DIGITS[c].w + 1
  }
  // Minecraft draws the level with a black outline: the glyphs offset in four directions, then green on top.
  const outline = [[-1, 0], [1, 0], [0, -1], [0, 1]]
    .map(([dx, dy]) => `<g fill="#000" transform="translate(${dx} ${dy})">${d}</g>`)
    .join('')
  return `${outline}<g fill="#80ff20">${d}</g>`
}

const svg = (w: number, h: number, inner: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges">${inner}</svg>`

type Stats = {
  week?: Limit
  five?: Limit
  ctxPercent: number
  ctxTokens?: number
  ctxWindow: number
  now: number
}

const pieces = (s: Stats) => {
  const xpFill = Math.floor((W * Math.min(100, s.ctxPercent)) / 100)
  return {
    heart: { w: ROW_W, h: 10, src: svg(ROW_W, 10, iconRow('heart', points(s.five?.percentUsed), false)) },
    level: { w: MID_W, h: 10, src: svg(MID_W, 10, s.ctxPercent > 0 ? levelText(s.ctxPercent) : '') },
    food: { w: ROW_W, h: 10, src: svg(ROW_W, 10, iconRow('food', points(s.week?.percentUsed), true)) },
    xp: {
      w: W,
      h: 5,
      src: svg(
        W,
        5,
        sprite('xp_bg', 0, 0) +
          `<clipPath id="xp"><rect x="0" y="0" width="${xpFill}" height="5"/></clipPath><g clip-path="url(#xp)">${sprite('xp_fg', 0, 0)}</g>`,
      ),
    },
  }
}

const half = (pts: number, i: number) => (pts - i * 2 >= 2 ? 2 : pts - i * 2 === 1 ? 1 : 0)

export const register: Register = on => {
  const stats = (u: SessionUsage, now: number): Stats => {
    const lim = (kind: string) => u.rateLimits.find(l => l.kind === kind)
    return {
      week: lim('seven_day'),
      five: lim('five_hour'),
      ctxPercent: Math.round(u.context.percent ?? 0),
      ctxTokens: u.context.tokens,
      ctxWindow: u.context.window,
      now,
    }
  }

  on('session.start', ($, e, next) => {
    $.clock.every(20000, () => $.ui.invalidate('ui.render'))
    return next(e)
  })

  on('turn.complete', ($, e, next) => {
    $.ui.invalidate('ui.render')
    return next(e)
  })

  on('prompt.submit', ($, e, next) => {
    $.ui.invalidate('ui.render')
    return next(e)
  })

  on('tool.call', ($, e, next) => {
    $.ui.invalidate('ui.render')
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)

    const s = stats(await $.session.usage(), await $.clock.now())
    const { Box, Text, Svg } = $.ui.resolve(e) as any

    if (e.surface !== 'terminal') {
      // Scale to the band's width (fractional, so it fills it) from its width in cells.
      const scale = Math.max(1, Math.min(MAX_SCALE, (e.props.bodyColumns * PX_PER_COLUMN * 0.985) / W))
      const px = (units: number) => Math.round(units * scale)
      const p = pieces(s)
      const draw = (key: keyof typeof p) => (
        <Svg source={p[key].src} alt={key} width={px(p[key].w)} height={px(p[key].h)} />
      )

      return (
        <Box flexDirection="column">
          <Box flexDirection="row">
            {draw('heart')}
            {draw('level')}
            {draw('food')}
          </Box>
          {draw('xp')}
        </Box>
      )
    }

    // Terminal: glyph version.
    const row = (full: string, halfG: string, empty: string, pts: number, rtl: boolean) => {
      let out = ''
      for (let i = 0; i < 10; i++) out += half(pts, i) === 2 ? full : half(pts, i) === 1 ? halfG : empty
      return rtl ? out.split('').reverse().join('') : out
    }
    const bar = Math.round(s.ctxPercent / 10)

    return (
      <Box gap={2}>
        <Text color="red">{row('♥', '♥', '♡', points(s.five?.percentUsed), false)}</Text>
        <Text color="yellow">{row('●', '◐', '○', points(s.week?.percentUsed), true)}</Text>
        <Text color="green">{`${'█'.repeat(bar)}${'░'.repeat(10 - bar)} ${s.ctxPercent}`}</Text>
      </Box>
    )
  })
}
