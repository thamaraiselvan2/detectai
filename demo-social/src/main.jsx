import { StrictMode, useEffect, useRef, useState } from 'react'
import { Check, ImagePlus, LockKeyhole, LogIn, Sparkles, UserRound, X } from 'lucide-react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function App() {
  const fileInputRef = useRef(null)
  const [mode, setMode] = useState('signup')
  const [form, setForm] = useState({ username: '', password: '', bio: '' })
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem('demo-social-user') || 'null')
    } catch {
      return null
    }
  })
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginMessage, setLoginMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [created, setCreated] = useState(false)

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview])

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
    setError('')
  }

  function updateLoginField(event) {
    setLoginForm((current) => ({ ...current, [event.target.name]: event.target.value }))
    setLoginError('')
    setLoginMessage('')
  }

  function chooseImage(event) {
    const selected = event.target.files?.[0]
    if (!selected) return

    if (preview) URL.revokeObjectURL(preview)
    setImage(selected)
    setPreview(URL.createObjectURL(selected))
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setError('')

    if (!image) {
      setError('Add a profile picture to continue.')
      return
    }

    setIsSubmitting(true)
    const payload = new FormData()
    payload.append('profile_picture', image)
    payload.append('username', form.username)
    payload.append('password', form.password)
    payload.append('bio', form.bio)

    try {
      const response = await fetch(`${API_URL}/api/social/create-account`, {
        method: 'POST',
        body: payload
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.message || 'Unable to create account.')
      setCreated(true)
    } catch (requestError) {
      setError(requestError.message || 'Unable to connect to the social network.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function login(event) {
    event.preventDefault()
    setLoginError('')
    setLoginMessage('')
    setIsLoggingIn(true)

    try {
      const response = await fetch(`${API_URL}/api/demo-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      })
      const result = await response.json()

      if (result.status === 'verification_required') {
        setLoginMessage(result.message || 'Additional device verification is required.')
        return
      }
      if (!response.ok || result.status !== 'success') {
        throw new Error(result.message || 'Unable to log in.')
      }

      sessionStorage.setItem('demo-social-user', JSON.stringify(result))
      setCurrentUser(result)
      setLoginForm({ username: '', password: '' })
    } catch (requestError) {
      setLoginError(requestError.message || 'Unable to connect to the social network.')
    } finally {
      setIsLoggingIn(false)
    }
  }

  function logout() {
    sessionStorage.removeItem('demo-social-user')
    setCurrentUser(null)
    setMode('login')
  }

  function closeSuccess() {
    setCreated(false)
    setForm({ username: '', password: '', bio: '' })
    setImage(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <main className="page-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <section className="signup-panel" aria-labelledby="page-title">
        <div className="brand-mark"><Sparkles size={16} strokeWidth={2.5} /> demo social</div>
        <div className="intro">
          <p className="eyebrow">A little corner of the internet</p>
          <h1 id="page-title">Make your profile<br /><em>feel like you.</em></h1>
          <p className="intro-copy">Set up a demo account and make your first impression count.</p>
        </div>

        {currentUser ? (
          <section className="account-panel" aria-live="polite">
            <div className="success-icon"><Check size={25} /></div>
            <p className="eyebrow">Signed in</p>
            <h2>@{currentUser.username}</h2>
            <p className="account-detail">Account ID: {currentUser.account_id}</p>
            <p className="account-detail">Registered email: {currentUser.registered_email || 'Not registered'}</p>
            <p className="account-detail">Device status: {currentUser.device_trust_status}</p>
            <button className="modal-button" type="button" onClick={logout}>Log out</button>
          </section>
        ) : (
          <>
            <div className="mode-switch" role="tablist" aria-label="Demo Social account access">
              <button type="button" className={mode === 'signup' ? 'active' : ''} onClick={() => { setMode('signup'); setLoginError(''); setLoginMessage('') }}>Create account</button>
              <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError('') }}>Log in</button>
            </div>

            {mode === 'signup' ? <form onSubmit={submit} noValidate>
          <div className="photo-picker">
            <button type="button" className="avatar-button" onClick={() => fileInputRef.current?.click()} aria-label="Choose a profile picture">
              {preview ? <img src={preview} alt="Selected profile preview" /> : <ImagePlus size={25} />}
            </button>
            <div>
              <p className="field-label">Profile picture</p>
              <p className="field-hint">Show the world who you are</p>
              <button type="button" className="upload-link" onClick={() => fileInputRef.current?.click()}>{image ? 'Choose another' : 'Upload an image'}</button>
            </div>
            <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml" onChange={chooseImage} hidden />
          </div>

          <label className="field"><span className="field-label">Username</span><span className="input-wrap"><UserRound size={18} /><input name="username" value={form.username} onChange={updateField} placeholder="Enter username" required /></span></label>
          <label className="field"><span className="field-label">Password</span><span className="input-wrap"><LockKeyhole size={18} /><input type="password" name="password" value={form.password} onChange={updateField} placeholder="Enter password" required /></span></label>
          <label className="field"><span className="field-label">Bio</span><textarea name="bio" value={form.bio} onChange={updateField} placeholder="Enter your bio" rows="4" required /></label>

          {error && <p className="error-message" role="alert">{error}</p>}
          <button className="submit-button" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating account...' : 'Create Account'} <span aria-hidden="true">↗</span></button>
            </form> : <form onSubmit={login} noValidate>
              <label className="field"><span className="field-label">Username</span><span className="input-wrap"><UserRound size={18} /><input name="username" value={loginForm.username} onChange={updateLoginField} placeholder="Enter username" required /></span></label>
              <label className="field"><span className="field-label">Password</span><span className="input-wrap"><LockKeyhole size={18} /><input type="password" name="password" value={loginForm.password} onChange={updateLoginField} placeholder="Enter password" required /></span></label>
              {loginError && <p className="error-message" role="alert">{loginError}</p>}
              {loginMessage && <p className="status-message" role="status">{loginMessage}</p>}
              <button className="submit-button" type="submit" disabled={isLoggingIn}><LogIn size={17} />{isLoggingIn ? 'Logging in...' : 'Log in'}</button>
            </form>}
          </>
        )}
      </section>

      {created && <div className="modal-backdrop" role="presentation"><section className="success-modal" role="dialog" aria-modal="true" aria-labelledby="success-title"><button className="close-button" onClick={closeSuccess} aria-label="Close success message"><X size={20} /></button><div className="success-icon"><Check size={25} /></div><p className="eyebrow">Welcome aboard</p><h2 id="success-title">Account Created Successfully</h2><p>Your demo profile has been added successfully.</p><button className="modal-button" onClick={closeSuccess}>Continue</button></section></div>}
    </main>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)