import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { userApi } from "../utils/api";
import { API_ENDPOINTS } from "../config/api";
import "./Profile.css";

const Profile = () => {
  const { user, logout, login } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        email: user.email || "",
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await userApi.put(API_ENDPOINTS.USER_PROFILE, formData);

      await login(response.data, null, null);

      setSuccess("پروفایل با موفقیت بروزرسانی شد!");
      setIsEditing(false);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "بروزرسانی پروفایل ناموفق بود. لطفاً دوباره تلاش کنید.",
      );
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div className="profile-container">در حال بارگذاری پروفایل...</div>;
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-header">
          <h1>پروفایل کاربر</h1>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {isEditing ? (
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-group">
              <label htmlFor="email">ایمیل</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                disabled
                className="form-control disabled"
              />
              <small className="text-muted">
                ایمیل به صورت مستقیم قابل تغییر نیست.
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="first_name">نام</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">نام خانوادگی</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="form-control"
              />
            </div>

            <div className="profile-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? "در حال ذخیره..." : "ذخیره تغییرات"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setIsEditing(false);
                  setError("");
                  setSuccess("");
                  setFormData({
                    first_name: user.first_name || "",
                    last_name: user.last_name || "",
                    email: user.email || "",
                  });
                }}
                disabled={loading}
              >
                انصراف
              </button>
            </div>
          </form>
        ) : (
          <div className="profile-content">
            <div className="profile-field">
              <label>ایمیل:</label>
              <span>{user.email}</span>
            </div>

            <div className="profile-field">
              <label>نام:</label>
              <span>{user.first_name || "-"}</span>
            </div>

            <div className="profile-field">
              <label>نام خانوادگی:</label>
              <span>{user.last_name || "-"}</span>
            </div>

            <div className="profile-actions">
              <button
                onClick={() => setIsEditing(true)}
                className="btn btn-primary"
              >
                ویرایش پروفایل
              </button>
              <button onClick={logout} className="btn btn-danger">
                خروج
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
