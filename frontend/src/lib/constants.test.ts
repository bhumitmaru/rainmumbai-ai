import { DISCLAIMER } from './constants'

test('disclaimer is probabilistic and does not guarantee outcomes', () => {
  expect(DISCLAIMER.toLowerCase()).toContain('probabilistic')
  expect(DISCLAIMER.toLowerCase()).toContain('do not guarantee future outcomes')
})
