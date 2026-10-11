import { render, screen } from '@testing-library/react'
import Disclaimer from './Disclaimer'

describe('Disclaimer', () => {
  it('renders the advisory text', () => {
    render(<Disclaimer />)
    expect(screen.getByText(/do not guarantee future outcomes/i)).toBeInTheDocument()
  })

  it('renders a custom message', () => {
    render(<Disclaimer text="Custom advisory." />)
    expect(screen.getByText(/Custom advisory/i)).toBeInTheDocument()
  })
})
