import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [stories, setStories] = useState([]);
  const [formData, setFormData] = useState({
    story: '',
    duration: 15,
    resolution: 'Full HD',
    tiktok: false
  });
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  // Fetch available stories on component mount
  useEffect(() => {
    fetchStories();
  }, []);

  // Poll job status when generating
  useEffect(() => {
    let interval;
    if (isGenerating && jobId) {
      interval = setInterval(() => {
        fetchJobStatus(jobId);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isGenerating, jobId]);

  const fetchStories = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stories`);
      setStories(response.data.stories);
      if (response.data.stories.length > 0) {
        setFormData(prev => ({ ...prev, story: response.data.stories[0] }));
      }
    } catch (err) {
      setError('Failed to fetch stories');
    }
  };

  const fetchJobStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status/${jobId}`);
      setJobStatus(response.data);
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        setIsGenerating(false);
      }
    } catch (err) {
      setError('Failed to fetch job status');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsGenerating(true);
    setJobStatus(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/generate`, formData);
      setJobId(response.data.job_id);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start video generation');
      setIsGenerating(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/download/${jobId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${formData.story}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download video');
    }
  };

  const resetForm = () => {
    setJobId(null);
    setJobStatus(null);
    setIsGenerating(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              AI Bible Story Video Generator
            </h1>
            <p className="text-lg text-gray-600">
              Create beautiful, AI-generated Bible story videos with narration and images
            </p>
          </div>

          {/* Main Form */}
          <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Story Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bible Story
                </label>
                <select
                  value={formData.story}
                  onChange={(e) => setFormData({ ...formData, story: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {stories.map((story) => (
                    <option key={story} value={story}>
                      {story}
                    </option>
                  ))}
                </select>
              </div>

              {/* Duration Slider */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration: {formData.duration} minutes
                </label>
                <input
                  type="range"
                  min="10"
                  max="25"
                  step="1"
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10 min</span>
                  <span>25 min</span>
                </div>
              </div>

              {/* Resolution Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Resolution
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['HD', 'Full HD', '4K'].map((res) => (
                    <button
                      key={res}
                      type="button"
                      onClick={() => setFormData({ ...formData, resolution: res })}
                      className={`py-2 px-4 rounded-md border font-medium transition-colors ${
                        formData.resolution === res
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {res}
                    </button>
                  ))}
                </div>
              </div>

              {/* TikTok Toggle */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="tiktok"
                  checked={formData.tiktok}
                  onChange={(e) => setFormData({ ...formData, tiktok: e.target.checked })}
                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                />
                <label htmlFor="tiktok" className="ml-2 text-sm font-medium text-gray-700">
                  Optimize for TikTok/Short Form (9:16 aspect ratio)
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isGenerating}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? 'Generating Video...' : 'Generate Video'}
              </button>
            </form>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Progress Section */}
          {jobStatus && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Video Generation Progress
              </h3>
              
              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-700 mb-2">
                  <span>Progress</span>
                  <span>{jobStatus.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${jobStatus.progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {jobStatus.status === 'processing' && (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2"></div>
                  )}
                  {jobStatus.status === 'completed' && (
                    <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {jobStatus.status === 'failed' && (
                    <svg className="h-5 w-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {jobStatus.status}
                  </span>
                </div>
                
                {jobStatus.status === 'completed' && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleDownload}
                      className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
                    >
                      Download Video
                    </button>
                    <button
                      onClick={resetForm}
                      className="bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 transition-colors"
                    >
                      Generate Another
                    </button>
                  </div>
                )}
              </div>

              {/* Error in job */}
              {jobStatus.error && (
                <div className="mt-4 p-3 bg-red-50 rounded-md">
                  <p className="text-sm text-red-700">{jobStatus.error}</p>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="text-center text-sm text-gray-500">
            <p>Powered by OpenAI, Replicate, ElevenLabs, and FFmpeg</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;