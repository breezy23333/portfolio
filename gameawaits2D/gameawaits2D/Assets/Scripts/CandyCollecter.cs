using UnityEngine;

public class CandyCollector : MonoBehaviour
{
    public ColorBarManager colorBarManager; // Will hook this up later

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Candy"))
        {
            string candyName = other.name.ToLower();

            // Add to color bar based on name
            if (candyName.Contains("red")) colorBarManager.AddColor("red");
            else if (candyName.Contains("blue")) colorBarManager.AddColor("blue");
            else if (candyName.Contains("green")) colorBarManager.AddColor("green");

            Debug.Log("🍬 Collected: " + other.name);
            Destroy(other.gameObject);
        }
    }
}
