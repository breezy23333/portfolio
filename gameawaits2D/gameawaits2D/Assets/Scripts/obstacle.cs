using UnityEngine;
using UnityEngine.SceneManagement;

public class ObstacleTrigger : MonoBehaviour
{
    void OnCollisionEnter2D(Collision2D other)
    {
        if (other.collider.CompareTag("Player"))
        {
            Debug.Log("💀 Player hit obstacle! Game Over.");
            // Reload scene for now (restart)
            SceneManager.LoadScene(SceneManager.GetActiveScene().name);
        }
    }
}