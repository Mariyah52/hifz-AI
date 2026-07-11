/**
 * Thin wrapper around the browser's native recording APIs. Kept free of
 * React state so it's independently testable — useRecorder owns the
 * stateful lifecycle, this file owns "how do I talk to the microphone."
 *
 * Requires a secure context (https, or localhost during development) —
 * that's a browser restriction on getUserMedia, not something this app
 * controls.
 */
export async function requestMicrophoneStream(): Promise<MediaStream> {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error('This browser does not support microphone recording.');
  }
  return navigator.mediaDevices.getUserMedia({ audio: true });
}

export function createRecorder(stream: MediaStream): MediaRecorder {
  return new MediaRecorder(stream);
}

export function stopStreamTracks(stream: MediaStream): void {
  stream.getTracks().forEach((track) => track.stop());
}
