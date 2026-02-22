using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class ColorBarManager : MonoBehaviour
{
    public Transform colorBarContainer;
    public GameObject colorBoxPrefab;

    private List<string> collectedColors = new List<string>();

    void Start()
    {
        AddColor("red");
        AddColor("green");
        AddColor("blue");
    }

    public void AddColor(string color)
    {
        collectedColors.Add(color);
        CreateColorBox(color);
        Debug.Log("✅ Added color: " + color);

        if (CheckForSet())
        {
            Debug.Log("🎉 Matching set complete!");
            // You can trigger effects here
        }
    }

    void CreateColorBox(string color)
    {
        GameObject newBox = Instantiate(colorBoxPrefab, colorBarContainer);
        Image img = newBox.GetComponent<Image>();

        if (img != null)
        {
            switch (color.ToLower())
            {
                case "red": img.color = Color.red; break;
                case "blue": img.color = Color.blue; break;
                case "green": img.color = Color.green; break;
                default: img.color = Color.white; break;
            }
        }
    }

    bool CheckForSet()
    {
        return collectedColors.Contains("red") &&
               collectedColors.Contains("blue") &&
               collectedColors.Contains("green");
    }
}